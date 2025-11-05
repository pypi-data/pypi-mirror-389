#include <iostream>
#include <sstream>
#include <algorithm>
#include <math.h>
#include "load_inst.hpp"
#include "utility.hpp"
#include "build_mdd.hpp"
#include "freq_miner.hpp"

namespace htminer {

using namespace std;

// ✅ Fix types here: M, mlim are unsigned int; N, L, theta, E are unsigned long long
unsigned int        M = 0, mlim = 0;
unsigned long long  N = 0, L = 0, theta = 0, E = 0;

bool itmset_exists = 0;

vector<int>      item_dic;
vector<Pattern>  DFS;
vector<VPattern> VDFS;

string out_file;
string folder;

bool b_disp     = 0;
bool b_write    = 0;
bool use_dic    = 0;
bool just_build = 0;
bool pre_pro    = 1;

unsigned int time_limit = 10 * 3600;
clock_t      start_time;

void Load_items_pre(string &inst_name);
bool Load_items(string &inst_name);
bool Preprocess(string& inst, double thresh);

bool Load_instance(string& items_file, double thresh) {

    clock_t kk = clock();

    Tree.emplace_back(0, 0, 0);

    if (pre_pro) {
        if (!Preprocess(items_file, thresh))
            return 0;
        if (b_disp)
           cout << "\nPreprocess done in " << give_time(clock() - kk) << " seconds\n\n";

        DFS.reserve((size_t)L);
        for (int i = 0; i < (int)L; ++i)
            DFS.emplace_back(-i - 1);

        kk = clock();

        Load_items_pre(items_file);
        if (Tree.size() > 100000000) {
            Tree.shrink_to_fit();
            CTree.shrink_to_fit();
            VTree.shrink_to_fit();
        }
    }
    else if (!Load_items(items_file))
        return 0;
    else {
        if (thresh < 1)
            theta = (unsigned long long)ceil(thresh * N);
        else
            theta = (unsigned long long)thresh;
    }
    if (b_disp)
      cout << "\nMDD Database built in " << give_time(clock() - kk) << " seconds\n\n";
    if (b_disp)
        cout << "Found " << N << " sequence, with max line len " << M
         << ", and " << L << " items, and " << E << " enteries\n";
    // cout << "Total Trie nodes: " << Tree.size()
    //      << " Total CTree nodes: " << CTree.size()
    //      << " Total VTree nodes: " << VTree.size() << endl;

    return 1;
}

bool Preprocess(string &inst, double thresh) {

    vector<unsigned long long int> MN(100, 0);
    vector<vector<bool>>           ML(100, vector<bool>(1000000, 0));

    ifstream file(inst);

    vector<unsigned int>           freq(1000000, 0);
    vector<unsigned long long int> counted(1000000, 0);

    if (file.good()) {
        string line;
        int    ditem;
        while (getline(file, line) &&
               give_time(clock() - start_time) < time_limit) {
            ++N;

            // if (N % 10000000 == 0) cout << "N: " << N << endl;
            istringstream word(line);
            string        itm;
            int           size_m = 0;
            while (word >> itm) {
                ++size_m;
                ditem = stoi(itm);

                if (ditem > 0)
                    itmset_exists = 1;
                else
                    ditem *= -1;

                if ((size_t)size_m < MN.size()) {
                    ++MN[size_m - 1];
                    if (ML[size_m - 1].size() < (size_t)ditem) {
                        ML[size_m - 1].reserve(ditem);
                        while (ML[size_m - 1].size() < (size_t)ditem)
                            ML[size_m - 1].push_back(0);
                    }
                    ML[size_m - 1][ditem - 1] = 1;
                }

                if (L < (unsigned long long)ditem)
                    L = (unsigned long long)ditem;

                if (freq.size() < (size_t)L) {
                    freq.reserve((size_t)L);
                    counted.reserve((size_t)L);
                    while (freq.size() < (size_t)L) {
                        freq.push_back(0);
                        counted.push_back(0);
                    }
                }

                if (counted[ditem - 1] != N) {
                    ++freq[ditem - 1];
                    counted[ditem - 1] = N;
                }

                ++E; // count entries
            }
            if (size_m > (int)M)
                M = (unsigned int)size_m;
        }
    }
    else {
        cout << "!!!!!! No such file exists: " << inst << " !!!!!!\n";
        return 0;
    }

    if (thresh < 1)
        theta = (unsigned long long)ceil(thresh * N);
    else
        theta = (unsigned long long)thresh;

    int         real_L = 0;
    item_dic = vector<int>((size_t)L, -1);
    vector<bool> item_in((size_t)L, 0);
    for (int i = 0; i < (int)L; ++i) {
        if (freq[i] >= theta) {
            item_dic[i] = ++real_L;
            item_in[i]  = 1;
        }
    }
    if (b_disp)
      cout << "Original number of items: " << L
         << " Reduced to: " << real_L << endl;

    unsigned long long int LpM = 1;
    mlim = M;
    int orgmlim;
    int ulim = std::min(3 + real_L / 5, 10);
    unsigned long long int ml;
    int coef = 1 + 1 * itmset_exists;
    for (int i = 0; i + ulim < (int)MN.size() && i + ulim < (int)M; ++i) {
        ml = 0;
        for (int j = 0; j < (int)L; ++j) {
            if (ML[i][j] && item_in[j])
                ++ml;
        }
        LpM *= ml * coef;
        // debug: ml, LpM, MN[i]
        // cout << ml << " " << LpM << " " << MN[i] << endl;
        if (LpM * ulim > MN[i]) {
            if (6 * (MN[i] - LpM) >= 5 * MN[i])
                orgmlim = i;
            while (i + ulim - 1 < (int)MN.size() && i + ulim - 1 < (int)M) {
                // debug: MN[i-1] - MN[i+ulim-1], MN[i+ulim-1]
                // cout << MN[i - 1] - MN[i + ulim - 1]
                //      << " " << MN[i + ulim - 1] << endl;
                if (MN[i - 1] - MN[i + ulim - 1] < MN[i + ulim - 1] &&
                    MN[i + ulim - 1] < 600000000) {
                    mlim = i - 1;
                    break;
                }
                i += 1;
            }
            break;
        }
    }

    // debug: final M/MLIM summary
    // cout << "M is: " << M << " Mlim is: " << mlim
    //      << " ulim is: " << ulim
    //      << " original mlim is: " << orgmlim
    //      << " guess is: "
    //      << round((log(N) - log(6)) / log(real_L)) << endl;

    if (mlim < M) {
        for (int i = 0; i < real_L; ++i)
            VDFS.emplace_back(i);
        if (MN[mlim + ulim] > 100000000) {
            CTree.reserve(MN[mlim + ulim] / 2);
            VTree.reserve(MN[mlim + ulim] / 2);
            Tree.reserve((N - MN[mlim + ulim]) * 2);
        }
    }
    else if (N > 100000000)
        Tree.reserve(500000000);

    L = (unsigned long long)real_L;
    N = 0;
    M = 0;

    return 1;
}


void Load_items_pre(string &inst_name) {

    ifstream file(inst_name);

    if (file.good()) {
        string line;
        int    ditem;
        while (getline(file, line) &&
               give_time(clock() - start_time) < time_limit) {
            istringstream word(line);
            string        itm;
            vector<int>   temp_vec;
            vector<int>   temp_lim;
            bool          sgn = 0;
            while (word >> itm) {

                ditem = stoi(itm);

                if (item_dic[std::abs(ditem) - 1] == -1) {
                    if (!sgn)
                        sgn = ditem < 0;
                    continue;
                }
                else {
                    if (ditem > 0)
                        ditem = item_dic[ditem - 1];
                    else
                        ditem = -item_dic[-ditem - 1];
                }

                if (sgn) {
                    if (ditem > 0)
                        ditem = -ditem;
                    sgn = 0;
                }

                if (temp_vec.size() <= mlim)
                    temp_vec.push_back(ditem);
                else
                    temp_lim.push_back(ditem);

                ++E;
            }

            if (temp_vec.empty())
                continue;

            ++N;
            // if (N % 1000000 == 0)
            //     cout << N << " " << Tree.size() << " " << CTree.size()
            //          << " " << VTree.size() << endl;

            if (temp_vec.size() + temp_lim.size() > M)
                M = (unsigned int)(temp_vec.size() + temp_lim.size());

            Build_MDD(temp_vec, temp_lim);
        }
    }
}

bool Load_items(string &inst_name) {

    ifstream file(inst_name);

    if (file.good()) {
        string line;
        int    ditem;
        while (getline(file, line) &&
               give_time(clock() - start_time) < time_limit) {
            ++N;
           // Optional progress print — only if verbose:
            // if (b_disp && N % 1000000 == 0)
                //cout << "Found " << N << " sequence, with max line len " << M
                     //<< ", and " << L << " items, and " << E
                    // << " enteries\n";

            istringstream word(line);
            string        itm;
            vector<int>   temp_vec;
            vector<int>   temp_lim;
            while (word >> itm) {
                ditem = stoi(itm);
                if (ditem > 0)
                    itmset_exists = 1;
                if (L < (unsigned long long)std::abs(ditem)) {
                    L = (unsigned long long)std::abs(ditem);
                    while (DFS.size() < (size_t)L) {
                        DFS.reserve((size_t)L);
                        DFS.emplace_back(-((int)DFS.size()) - 1);
                    }
                }

                if (temp_vec.size() < mlim)
                    temp_vec.push_back(ditem);
                else
                    temp_lim.push_back(ditem);

                ++E;
            }

            if (temp_vec.size() + temp_lim.size() > M)
                M = (unsigned int)(temp_vec.size());

            Build_MDD(temp_vec, temp_lim);
        }
    }
    else {
        cout << "!!!!!! No such file exists: " << inst_name << " !!!!!!\n";
        return 0;
    }

    return 1;
}

} // namespace htminer
