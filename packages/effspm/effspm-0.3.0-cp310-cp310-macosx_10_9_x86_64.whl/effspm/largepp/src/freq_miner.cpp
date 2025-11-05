#include <algorithm>
#include <cstdlib>
#include <fstream>
#include <iostream>

#include "freq_miner.hpp"
#include "pattern.hpp"
#include "load_inst.hpp"
#include "utility.hpp"

namespace largepp {

using std::abs;
using std::cout;
using std::endl;
using std::ofstream;
using std::swap;
using std::vector;

static void Out_patt(vector<int>& seq, unsigned int freq);
static void Extend_patt(Pattern& _pattern);

unsigned long long int num_patt = 0;      // counter for emitted patterns
static Pattern _patt;                     // scratch pattern (for in-place extend)

/* ------------------------------------------------------------------ */
/*  Driver                                                            */
/* ------------------------------------------------------------------ */
void Freq_miner()
{
    // Build the candidate item list once (items that pass minsup at length-1)
    vector<int> islist;
    islist.reserve(L);
    for (unsigned int i = 0; i < L; ++i) {
        if (DFS[i].freq >= theta) islist.push_back(static_cast<int>(i));
    }

    // Seed each 1-length pattern’s extension lists
    for (unsigned int i = 0; i < DFS.size(); ++i) {
        DFS[i].ilist = islist;
        DFS[i].slist = islist;
    }

    // DFS over the stack, extending only nodes whose current support ≥ theta
    while (!DFS.empty() && give_time(std::clock() - start_time) < time_limit) {
        if (DFS.back().freq >= theta) {
            Extend_patt(DFS.back());
        } else {
            DFS.pop_back();
        }
    }
}

/* ------------------------------------------------------------------ */
/*  Extend_patt: given a frequent pattern, enumerate its i- and s-ext */
/* ------------------------------------------------------------------ */
static void Extend_patt(Pattern& _pattern)
{
    swap(_patt, _pattern);  // work on local scratch
    DFS.pop_back();         // remove from stack

    // Quick presence tables for allowed i-/s-extensions
    vector<bool> slist(L, false);
    vector<bool> ilist(L, false);
    for (int idx : _patt.slist) slist[static_cast<size_t>(idx)] = true;
    for (int idx : _patt.ilist) ilist[static_cast<size_t>(idx)] = true;

    // Potential children buffers:
    vector<Pattern> pot_patt(L * 2); // [0..L-1] = i-ext, [L..2L-1] = s-ext

    // Find last negative from the end (boundary between itemsets)
    int last_neg = static_cast<int>(_patt.seq.size()) - 1;
    while (last_neg >= 0 && _patt.seq[static_cast<size_t>(last_neg)] > 0) --last_neg;

    // Scan occurrences to build supports for all valid next-steps
    for (size_t i = 0; i < _patt.str_pnt.size(); ++i) {
        vector<bool> found(L * 2, false);

        unsigned long long seq_id = _patt.seq_ID[i];
        unsigned int j = _patt.str_pnt[i] + 1;

        // 1) Same itemset (i-extension) forward until end-of-itemset (>0)
        while (j < items[seq_id].size() && items[seq_id][j] > 0) {
            int cur_itm = items[seq_id][j];
            if (ilist[static_cast<size_t>(cur_itm - 1)]) {
                pot_patt[static_cast<size_t>(cur_itm - 1)].seq_ID.push_back(seq_id);
                pot_patt[static_cast<size_t>(cur_itm - 1)].str_pnt.push_back(j);
                ++pot_patt[static_cast<size_t>(cur_itm - 1)].freq;
                found[static_cast<size_t>(cur_itm - 1)] = true;
            }
            ++j;
        }

        // 2) Later itemsets (s-extension), plus special re-open i-ext rule
        int num_itmfnd = 0;
        for (size_t k = j; k < items[seq_id].size(); ++k) {
            int cur = items[seq_id][k];
            int cur_itm = abs(cur);

            if (cur < 0) num_itmfnd = 0; // new itemset boundary seen

            // s-extension: add cur_itm as new itemset element
            if (slist[static_cast<size_t>(cur_itm - 1)] &&
                !found[static_cast<size_t>(L + cur_itm - 1)]) {
                pot_patt[static_cast<size_t>(L + cur_itm - 1)].seq_ID.push_back(seq_id);
                pot_patt[static_cast<size_t>(L + cur_itm - 1)].str_pnt.push_back(k);
                ++pot_patt[static_cast<size_t>(L + cur_itm - 1)].freq;
                found[static_cast<size_t>(L + cur_itm - 1)] = true;
            }

            // once we've seen the suffix of the last itemset fully,
            // allow i-extension again (across future itemsets)
            if (num_itmfnd == static_cast<int>(_patt.seq.size()) - last_neg) {
                if (ilist[static_cast<size_t>(cur_itm - 1)] &&
                    !found[static_cast<size_t>(cur_itm - 1)]) {
                    pot_patt[static_cast<size_t>(cur_itm - 1)].seq_ID.push_back(seq_id);
                    pot_patt[static_cast<size_t>(cur_itm - 1)].str_pnt.push_back(k);
                    ++pot_patt[static_cast<size_t>(cur_itm - 1)].freq;
                    found[static_cast<size_t>(cur_itm - 1)] = true;
                }
            } else if (last_neg + num_itmfnd >= 0 &&
                       cur_itm == abs(_patt.seq[static_cast<size_t>(last_neg + num_itmfnd)])) {
                ++num_itmfnd;
            }
        }
    }

    // Filter children by support threshold
    vector<int> ilistp;
    vector<int> slistp;
    ilistp.reserve(_patt.ilist.size());
    slistp.reserve(_patt.slist.size());

    for (int idx : _patt.ilist) {
        if (pot_patt[static_cast<size_t>(idx)].freq >= theta)
            ilistp.push_back(idx);
    }
    for (int idx : _patt.slist) {
        if (pot_patt[static_cast<size_t>(idx + static_cast<int>(L))].freq >= theta)
            slistp.push_back(idx);
    }

    // Push all i-extensions
    for (int idx : ilistp) {
        DFS.emplace_back();
        swap(DFS.back(), pot_patt[static_cast<size_t>(idx)]);

        DFS.back().seq = _patt.seq;
        DFS.back().seq.push_back(idx + 1);

        DFS.back().slist = slistp;
        DFS.back().ilist = ilistp;

        // ALWAYS emit (so collected fills even if !b_disp && !b_write)
        Out_patt(DFS.back().seq, DFS.back().freq);
        ++num_patt;
    }

    // Push all s-extensions
    for (int idx : slistp) {
        DFS.emplace_back();
        swap(DFS.back(), pot_patt[static_cast<size_t>(idx + static_cast<int>(L))]);

        DFS.back().seq = _patt.seq;
        DFS.back().seq.push_back(-(idx + 1));  // negative encodes new itemset

        DFS.back().slist = slistp;
        DFS.back().ilist = slistp;             // as in original code

        // ALWAYS emit
        Out_patt(DFS.back().seq, DFS.back().freq);
        ++num_patt;
    }
}

/* ------------------------------------------------------------------ */
/*  Out_patt: append to buffer; optionally print/write                */
/* ------------------------------------------------------------------ */
static void Out_patt(vector<int>& seq, unsigned int freq)
{
    // Always append to in-memory results returned to Python
    largepp::collected.push_back(seq);

    ofstream file_o;
    if (b_write) file_o.open(out_file, std::ios::app);

    if (b_disp) {
        for (int v : seq) cout << v << " ";
        cout << "\n************** Freq: " << freq << endl;
    }
    if (b_write) {
        for (int v : seq) file_o << v << " ";
        file_o << "\n************** Freq: " << freq << "\n";
        file_o.close();
    }
}

} // namespace largepp
