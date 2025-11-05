#include <iostream>
#include <sstream>
#include <algorithm>
#include <cmath>
#include <fstream>
#include "load_inst.hpp"
#include "freq_miner.hpp"
#include "utility.hpp"

namespace largepp {   // ─── BEGIN namespace ─────────────────────
using namespace std;

/* ------------------------------------------------------------------
 *  Global definitions (match the externs in load_inst.hpp)
 * ---------------------------------------------------------------- */
unsigned int        M = 0, L = 0;
unsigned long long  N = 0, E = 0;
double              theta = 0.01;
vector<vector<int>> items;
vector<Pattern>     DFS;
vector<int>         item_dic;

/*  Forward decls for helper routines in this file  */
static bool  Load_items(string& inst);
static void  Load_items_pre(string& inst);
static bool  Preprocess(string& inst, double thresh);

/* ==================================================================
 *  MAIN ENTRY — load from disk
 * ================================================================= */
bool Load_instance(string& items_file, double thresh)
{
    clock_t kk = clock();

    if (pre_pro) {
        if (!Preprocess(items_file, thresh)) return false;

        cout << "\nPreprocess done in " << give_time(clock() - kk) << " seconds\n\n";

        DFS.clear();
        DFS.reserve(L);
        for (unsigned int i = 0; i < L; ++i)
            DFS.emplace_back(-int(i) - 1);

        kk = clock();
        Load_items_pre(items_file);
        N = items.size();
    }
    else if (!Load_items(items_file))
        return false;
    else
        theta = (thresh < 1.0) ? ceil(thresh * N) : thresh;

    cout << "\nMDD Database built in " << give_time(clock() - kk) << " seconds\n\n";
    cout << "Found " << N << " sequence, with max line len " << M
         << ", and " << L << " items, and " << E << " enteries\n";

    // ───────────────────────────────────────────────────────────
    // DEBUG snapshot of seeds right after loading
    // ───────────────────────────────────────────────────────────
    {
        unsigned long long seeds_ge_theta = 0, seeds_nonzero = 0, max_freq = 0;
        for (size_t i = 0; i < DFS.size(); ++i) {
            if (DFS[i].freq > 0) ++seeds_nonzero;
            if (DFS[i].freq >= theta) ++seeds_ge_theta;
            if (DFS[i].freq > max_freq) max_freq = DFS[i].freq;
        }
       // std::cout << " theta=" << theta
               //   << " | DFS.size=" << DFS.size()
               //   << " | seeds>=theta=" << seeds_ge_theta
              //    << " | seeds>0=" << seeds_nonzero
              //    << " | max_seed_freq=" << max_freq << "\n";
    }

    return true;
}

/* ==================================================================
 *  ALT ENTRY — load directly from a Python list of lists
 * ================================================================= */
void Load_py(const pybind11::object& data, double thresh)
{
    items = data.cast<vector<vector<int>>>();
    N     = items.size();

    int max_id = 0;
    M = 0;  E = 0;
    for (auto& seq : items) {
        M = max<unsigned int>(M, static_cast<unsigned int>(seq.size()));
        E += seq.size();
        for (int x : seq)
            max_id = max(max_id, abs(x));
    }
    L = static_cast<unsigned int>(max_id);
    theta = (thresh < 1.0) ? ceil(thresh * N) : thresh;

    DFS.clear();
    DFS.reserve(L);
    for (unsigned int i = 0; i < L; ++i)
        DFS.emplace_back(-int(i) - 1);
}

/* =================================================================
 *  The professor’s original helpers — untouched except minor safety
 * ================================================================= */
static bool Preprocess(string& inst, double thresh)
{
    ifstream file(inst);
    vector<unsigned long long> freq(1000000), counted(1000000, 0);

    if (file.good()) {
        string line; int ditem;
        while (getline(file, line) && give_time(clock() - start_time) < time_limit) {
            ++N;
            istringstream word(line);
            string itm;
            while (word >> itm) {
                ditem = stoi(itm);
                L = max<unsigned int>(L, static_cast<unsigned int>(abs(ditem)));

                if (freq.size() < L) {
                    freq.resize(L, 0);
                    counted.resize(L, 0);
                }
                if (counted[abs(ditem) - 1] != N) {
                    ++freq[abs(ditem) - 1];
                    counted[abs(ditem) - 1] = N;
                }
            }
        }
    } else {
        cout << "!!!!!! No such file exists: " << inst << " !!!!!!\n";
        return false;
    }

    theta = (thresh < 1.0) ? ceil(thresh * N) : thresh;

    int real_L = 0;
    item_dic.assign(L, -1);
    for (unsigned int i = 0; i < L; ++i)
        if (freq[i] >= theta) item_dic[i] = ++real_L;

    cout << "Original number of items: " << L
         << "  Reduced to: " << real_L << '\n';

    L = real_L;
    N = 0;
    return true;
}

static void Load_items_pre(string& inst)
{
    ifstream file(inst);

    if (!file.good()) return;
    string line; int size_m, ditem; bool empty_seq = false;

    while (getline(file, line) && give_time(clock() - start_time) < time_limit) {
        vector<bool> counted(L, 0);
        istringstream word(line);

        if (!empty_seq) items.emplace_back();
        string itm; size_m = 0; bool sgn = false; empty_seq = true;

        while (word >> itm) {
            ditem = stoi(itm);

            if (item_dic[abs(ditem) - 1] == -1) {
                if (!sgn) sgn = ditem < 0;
                continue;
            } else {
                ditem = (ditem > 0)
                      ?  item_dic[ditem - 1]
                      : -item_dic[-ditem - 1];
            }
            empty_seq = false;

            if (sgn) { if (ditem > 0) ditem = -ditem; sgn = false; }

            items.back().push_back(ditem);

            if (!counted[abs(ditem) - 1] && !just_build) {
                DFS[abs(ditem) - 1].seq_ID.push_back(items.size() - 1);
                DFS[abs(ditem) - 1].str_pnt.push_back(items.back().size() - 1);
                ++DFS[abs(ditem) - 1].freq;
                counted[abs(ditem) - 1] = true;
            }
            ++size_m;
        }
        if (empty_seq) continue;

        ++N;  E += size_m;  M = max<unsigned int>(M, static_cast<unsigned int>(size_m));
    }
}

static bool Load_items(string& inst)
{
    ifstream file(inst);
    if (!file.good()) {
        cout << "!!!!!! No such file exists: " << inst << " !!!!!!\n";
        return false;
    }

    string line; int size_m, ditem;
    while (getline(file, line) && give_time(clock() - start_time) < time_limit) {
        ++N;
        vector<bool> counted(L, 0);
        istringstream word(line);

        items.emplace_back();
        string itm; size_m = 0;

        while (word >> itm) {
            ditem = stoi(itm);
            if (L < static_cast<unsigned int>(abs(ditem))) {
                L = static_cast<unsigned int>(abs(ditem));
                while (DFS.size() < L) {
                    DFS.emplace_back(-int(DFS.size()) - 1);
                    counted.push_back(0);
                }
            }
            items.back().push_back(ditem);

            if (!counted[abs(ditem) - 1] && !just_build) {
                DFS[abs(ditem) - 1].seq_ID.push_back(items.size() - 1);
                DFS[abs(ditem) - 1].str_pnt.push_back(items.back().size() - 1);
                ++DFS[abs(ditem) - 1].freq;
                counted[abs(ditem) - 1] = true;
            }
            ++size_m;
        }
        E += size_m;
        M = max<unsigned int>(M, static_cast<unsigned int>(size_m));
    }
    return true;
}

} // namespace largepp  // ─── END namespace ──────────────────────
