#include <algorithm>
#include <fstream>
#include <iostream>
#include <unordered_map>
#include <unordered_set>
#include <cstdlib>  // ensure std::abs(int)
#include "freq_miner.hpp"
#include "load_inst.hpp"
#include "utility.hpp"
#include "build_mdd.hpp"

namespace largebm {

unsigned long long int num_patt = 0;
std::vector<bool> ilist;
std::vector<bool> slist;
std::vector<int>  DFS_numfound;
Pattern            _patt;

static void Out_patt(const std::vector<int>& seq, unsigned long long freq);
static void Extend_patt(Pattern& patt);

void Freq_miner() {
    collected.clear();
    num_patt = 0;

    if (static_cast<int>(DFS.size()) < static_cast<int>(L)) {
        DFS.resize(L);
    }

    std::vector<int> list;

    if (use_list) {
        std::vector<int> empty_pref;
        Freq_miner_list(items, empty_pref, theta, collected);
        return;
    }

    // seed candidates by DFS[i].freq
    for (int i = 0; i < static_cast<int>(L); ++i) {
        if (DFS[i].freq >= theta) {
            list.push_back(-i - 1);
            if (itmset_exists) list.push_back(i + 1);
        }
    }

    for (size_t i = 0; i < DFS.size(); ++i) {
        DFS[i].list = list;
    }

    while (!DFS.empty() && give_time(std::clock() - start_time) < time_limit) {
        if (DFS.back().freq >= theta) {
            Extend_patt(DFS.back());
        } else {
            DFS.pop_back();
        }
    }
}

static void Extend_patt(Pattern& _pattern) {
    std::swap(_patt, _pattern);
    DFS.pop_back();

    slist = std::vector<bool>(L, false);
    bool ilist_nempty = false;

    if (itmset_exists) {
        ilist = std::vector<bool>(L, false);
        for (size_t i = 0; i < _patt.list.size(); ++i) {
            int v = _patt.list[i];
            if (v < 0) slist[-v - 1] = true;
            else { ilist[v - 1] = true; ilist_nempty = true; }
        }
    } else {
        for (size_t i = 0; i < _patt.list.size(); ++i) {
            int v = _patt.list[i];
            slist[-v - 1] = true;
        }
    }

    int itmset_size = 1;
    int last_neg = static_cast<int>(_patt.seq.size()) - 1;
    while (_patt.seq[last_neg] > 0) {
        --last_neg;
        ++itmset_size;
    }

    std::vector<Pattern>               pot_patt(L + (ilist_nempty ? L : 0));
    std::vector<unsigned long long>    DFS_patt_init;
    std::vector<unsigned long long>    DFS_patt;
    if (ilist_nempty) DFS_numfound.clear();
    std::vector<unsigned long long>    last_strpnt(L, 0);

    for (unsigned long long pnt = 0; pnt < _patt.str_pnt.size(); ++pnt) {
        DFS_patt_init.push_back(_patt.str_pnt[pnt]);
        while (!DFS_patt_init.empty()) {
            unsigned long long cur_sibl = Tree[DFS_patt_init.back()].chld;
            DFS_patt_init.pop_back();
            while (cur_sibl != 0) {
                int cur_itm = Tree[cur_sibl].item;
                if (cur_itm < 0) {
                    cur_itm = -cur_itm;
                    if (slist[cur_itm - 1]) {
                        pot_patt[cur_itm - 1].freq += Tree[cur_sibl].freq;
                        if (Tree[cur_sibl].chld != 0)
                            pot_patt[cur_itm - 1].str_pnt.push_back(cur_sibl);
                    }
                    if (Tree[cur_sibl].chld != static_cast<unsigned long long>(-1)) {
                        DFS_patt.push_back(cur_sibl);
                        if (ilist_nempty) {
                            DFS_numfound.push_back(cur_itm == -_patt.seq[last_neg] ? 1 : 0);
                        }
                    }
                } else {
                    if (ilist[cur_itm - 1]) {
                        pot_patt[cur_itm + L - 1].freq += Tree[cur_sibl].freq;
                        if (Tree[cur_sibl].chld != 0)
                            pot_patt[cur_itm + L - 1].str_pnt.push_back(cur_sibl);
                    }
                    if (Tree[cur_sibl].chld != static_cast<unsigned long long>(-1))
                        DFS_patt_init.push_back(cur_sibl);
                }
                cur_sibl = Tree[cur_sibl].sibl;
            }
        }
        if (ilist_nempty) {
            for (int i = 0; i < static_cast<int>(L); ++i) {
                if (ilist[i]) last_strpnt[i] = pot_patt[i + L].str_pnt.size();
            }
        }
        while (!DFS_patt.empty()) {
            unsigned long long cur_sibl = Tree[DFS_patt.back()].chld;
            DFS_patt.pop_back();
            int num_found = 0;
            if (ilist_nempty) { num_found = DFS_numfound.back(); DFS_numfound.pop_back(); }
            while (cur_sibl != 0) {
                int cur_itm = Tree[cur_sibl].item;
                if (cur_itm > 0) {
                    if (num_found == itmset_size &&
                        ilist[cur_itm - 1] &&
                        (Tree[Tree[cur_sibl].anct].itmset < Tree[_patt.str_pnt[pnt]].itmset ||
                         !check_parent(cur_sibl, _patt.str_pnt[pnt],
                                       last_strpnt[cur_itm - 1],
                                       pot_patt[cur_itm + L - 1].str_pnt))) {
                        pot_patt[cur_itm + L - 1].freq += Tree[cur_sibl].freq;
                        if (Tree[cur_sibl].chld != 0)
                            pot_patt[cur_itm + L - 1].str_pnt.push_back(cur_sibl);
                    }
                    if (slist[cur_itm - 1] &&
                        Tree[Tree[cur_sibl].anct].itmset <= Tree[_patt.str_pnt[pnt]].itmset) {
                        pot_patt[cur_itm - 1].freq += Tree[cur_sibl].freq;
                        if (Tree[cur_sibl].chld != 0)
                            pot_patt[cur_itm - 1].str_pnt.push_back(cur_sibl);
                    }
                    if (Tree[cur_sibl].chld != static_cast<unsigned long long>(-1)) {
                        DFS_patt.push_back(cur_sibl);
                        if (ilist_nempty) {
                            if (num_found < itmset_size &&
                                cur_itm == std::abs(_patt.seq[last_neg + num_found])) {
                                DFS_numfound.push_back(num_found + 1);
                            } else {
                                DFS_numfound.push_back(num_found);
                            }
                        }
                    }
                } else {
                    cur_itm = -cur_itm;
                    if (slist[cur_itm - 1] &&
                        Tree[Tree[cur_sibl].anct].itmset <= Tree[_patt.str_pnt[pnt]].itmset) {
                        pot_patt[cur_itm - 1].freq += Tree[cur_sibl].freq;
                        if (Tree[cur_sibl].chld != 0)
                            pot_patt[cur_itm - 1].str_pnt.push_back(cur_sibl);
                    }
                    if (Tree[cur_sibl].chld != static_cast<unsigned long long>(-1)) {
                        DFS_patt.push_back(cur_sibl);
                        if (ilist_nempty) {
                            DFS_numfound.push_back(cur_itm == -_patt.seq[last_neg] ? 1 : 0);
                        }
                    }
                }
                cur_sibl = Tree[cur_sibl].sibl;
            }
        }
    }

    std::vector<int> ilistp;
    std::vector<int> slistp;
    for (size_t i = 0; i < _patt.list.size(); ++i) {
        int v = _patt.list[i];
        int idx = (v < 0) ? (-v - 1) : (v - 1 + static_cast<int>(L));
        if (v > 0 && pot_patt[idx].freq >= theta) {
            ilistp.push_back(v);
        } else if (v < 0 && pot_patt[-v - 1].freq >= theta) {
            if (itmset_exists) slistp.push_back(-v);
            ilistp.push_back(v);
            slistp.push_back(v);
        }
    }

    for (size_t i = 0; i < ilistp.size(); ++i) {
        int v = ilistp[i];
        int p = (v < 0) ? (-v - 1) : (v - 1 + static_cast<int>(L));
        DFS.emplace_back();
        std::swap(DFS.back(), pot_patt[p]);
        DFS.back().seq = _patt.seq;
        DFS.back().seq.push_back(v);
        DFS.back().list = (v < 0) ? slistp : ilistp;
        Out_patt(DFS.back().seq, DFS.back().freq);
        ++num_patt;
    }
}

static void Out_patt(const std::vector<int>& seq, unsigned long long freq) {
    if (!(b_disp || b_write)) {
        collected.push_back(seq);
        return;
    }
    std::ofstream file_o;
    if (b_write) file_o.open(out_file, std::ios::app);

    for (size_t i = 0; i < seq.size(); ++i) {
        int v = seq[i];
        if (b_disp) std::cout << v << ' ';
        if (b_write) file_o << v << ' ';
    }
    if (b_disp) std::cout << '\n';
    if (b_write) file_o << '\n';

    if (b_disp) std::cout << "************** Freq: " << freq << '\n';
    if (b_write) {
        file_o << "************** Freq: " << freq << '\n';
        file_o.close();
    }
    collected.push_back(seq);
}

void Freq_miner_list(const std::vector<std::vector<int>>& db,
                     std::vector<int>& prefix,
                     unsigned long long minsup,
                     std::vector<std::vector<int>>& out) {
    std::unordered_map<int, unsigned long long> freq;
    for (size_t sidx = 0; sidx < db.size(); ++sidx) {
        const std::vector<int>& seq = db[sidx];
        std::unordered_set<int> seen;
        for (size_t i = 0; i < seq.size(); ++i) {
            int x = seq[i];
            if (seen.insert(x).second) ++freq[x];
        }
    }

    std::vector<std::pair<int, unsigned long long> > cand;
    cand.reserve(freq.size());
    for (std::unordered_map<int, unsigned long long>::iterator it = freq.begin();
         it != freq.end(); ++it) {
        if (it->second >= minsup) cand.push_back(*it);
    }

    std::sort(cand.begin(), cand.end(),
              [](const std::pair<int, unsigned long long>& a,
                 const std::pair<int, unsigned long long>& b) {
                  return std::abs(a.first) < std::abs(b.first);
              });

    for (size_t k = 0; k < cand.size(); ++k) {
        int item = cand[k].first;
        prefix.push_back(item);

        if (use_dic) {
            std::vector<int> unmapped;
            unmapped.reserve(prefix.size());
            for (size_t i = 0; i < prefix.size(); ++i) {
                int cid = prefix[i];
                int abs_id = std::abs(cid);
                int o = inv_item_dic[abs_id];
                unmapped.push_back(cid < 0 ? -o : o);
            }
            out.push_back(unmapped);
        } else {
            out.push_back(prefix);
        }

        std::vector<std::vector<int> > proj;
        proj.reserve(db.size());
        for (size_t s = 0; s < db.size(); ++s) {
            const std::vector<int>& svec = db[s];
            std::vector<int>::const_iterator it =
                std::find(svec.begin(), svec.end(), item);
            if (it != svec.end()) {
                ++it;
                if (it != svec.end()) proj.push_back(std::vector<int>(it, svec.end()));
            }
        }

        if (!proj.empty()) Freq_miner_list(proj, prefix, minsup, out);
        prefix.pop_back();
    }
}

} // namespace largebm
