// ─── effspm/largehm/src/load_inst.cpp ────────────────────────────────────────

#include <iostream>
#include <sstream>
#include <algorithm>
#include <fstream>
#include <cmath>
#include <ctime>

#include "load_inst.hpp"
#include "utility.hpp"
#include "build_mdd.hpp"
#include "freq_miner.hpp"

namespace largehm {
using namespace std;

string out_file;
string folder;

bool b_disp        = false;
bool b_write       = false;
bool use_dic       = false;
bool use_list      = false;
bool just_build    = false;
bool pre_pro       = false;
bool itmset_exists = false;

unsigned int M          = 0;
unsigned int L          = 0;
unsigned int mlim       = 0;
unsigned int time_limit = 0;

unsigned long long int N     = 0;
unsigned long long int theta = 0;
unsigned long long int E     = 0;

clock_t start_time = 0;

vector<vector<int>> items;

vector<int>     item_dic;
vector<Pattern> DFS;
vector<VPattern> VDFS;


// ─────────────────────────────────────────────────────────────────────────────
// Load_instance
// ─────────────────────────────────────────────────────────────────────────────
bool Load_instance(string& items_file, double thresh) {
    // 1) CLEAR leftover state
    Tree.clear();
    VTree.clear();
    CTree.clear();
    DFS.clear();
    VDFS.clear();
    item_dic.clear();
    items.clear();

    N = 0;
    M = 0;
    L = 0;
    E = 0;
    theta = 0;
    itmset_exists = false;

    clock_t kk = clock();

    // root
    Tree.emplace_back(0, 0, 0);

    if (!pre_pro) {
        if (!Load_items(items_file))
            return false;

        DFS.reserve(L);
        while (DFS.size() < L)
            DFS.emplace_back(-static_cast<int>(DFS.size()) - 1);

        VDFS.reserve(L);
        while (VDFS.size() < L)
            VDFS.emplace_back(static_cast<int>(VDFS.size()));

        if (thresh < 1.0)
            theta = static_cast<unsigned long long>(ceil(thresh * N));
        else
            theta = static_cast<unsigned long long>(thresh);

        start_time = clock();
    }
    else {
        if (!Load_items(items_file))
            return false;

        if (thresh < 1.0)
            theta = static_cast<unsigned long long>(ceil(thresh * N));
        else
            theta = static_cast<unsigned long long>(thresh);

        start_time = clock();
    }

    // 👇 only print when verbose/b_disp
    if (b_disp) {
        cout << "\nMDD Database built in " << give_time(clock() - kk) << " seconds\n\n";
        cout << "Found " << N << " sequence, with max line len " << M
             << ", and " << L << " items, and " << E << " enteries\n";
        // cout << "Total Trie nodes: " << Tree.size()
        //      << " Total CTree nodes: " << CTree.size()
        //      << " Total VTree nodes: " << VTree.size() << endl;
    }

    return true;
}


// ─────────────────────────────────────────────────────────────────────────────
// Preprocess
// ─────────────────────────────────────────────────────────────────────────────
bool Preprocess(string &inst, double thresh) {
    vector<unsigned long long int> MN(100, 0);
    vector<vector<bool>> ML(100, vector<bool>(1000000, false));

    ifstream file(inst);
    if (!file.good()) {
        if (b_disp)
            cout << "!!!!!! No such file exists: " << inst << " !!!!!!\n";
        return false;
    }

    vector<unsigned long long int> freq(1000000, 0ULL);
    vector<unsigned long long int> counted(1000000, 0ULL);

    string line;
    int ditem;
    while (getline(file, line) && give_time(clock() - start_time) < time_limit) {
        ++N;
        if (b_disp && N % 10000000 == 0)
            cout << "N: " << N << endl;

        istringstream word(line);
        string itm;
        int size_m = 0;
        while (word >> itm) {
            ++size_m;
            ditem = stoi(itm);

            if (ditem > 0)
                itmset_exists = true;
            else
                ditem = -ditem;

            if (size_m < (int)MN.size()) {
                ++MN[size_m - 1];
                if ((int)ML[size_m - 1].size() < ditem) {
                    ML[size_m - 1].resize(ditem, false);
                }
                ML[size_m - 1][ditem - 1] = true;
            }

            if (L < static_cast<unsigned int>(ditem)) {
                L = static_cast<unsigned int>(ditem);
            }

            if ((int)freq.size() < ditem) {
                freq.resize(ditem, 0ULL);
                counted.resize(ditem, 0ULL);
            }
            if (counted[ditem - 1] != N) {
                ++freq[ditem - 1];
                counted[ditem - 1] = N;
            }
        }
        if (size_m > (int)M)
            M = size_m;
    }

    if (thresh < 1.0)
        theta = static_cast<unsigned long long>(ceil(thresh * N));
    else
        theta = static_cast<unsigned long long>(thresh);

    int real_L = 0;
    item_dic.assign(L, -1);
    vector<bool> item_in(L, false);
    for (int i = 0; i < (int)L; ++i) {
        if (freq[i] >= theta) {
            item_dic[i] = ++real_L;
            item_in[i]  = true;
        }
    }

    if (b_disp)
        cout << "Original number of items: " << L << " Reduced to: " << real_L << endl;

    unsigned long long int LpM = 1;
    mlim = M;
    int orgmlim = 0;
    int ulim = min(1 + real_L / 4, 10);
    unsigned long long int ml;

    for (int i = 0; i + ulim < (int)MN.size() && i + ulim < (int)M; ++i) {
        ml = 0;
        for (int j = 0; j < (int)L; ++j) {
            if (ML[i][j] && item_in[j])
                ++ml;
        }
        LpM *= ml * (1 + itmset_exists);

        if (b_disp)
            cout << ml << " " << LpM << " " << MN[i] << endl;

        if (LpM * ulim > MN[i]) {
            orgmlim = i;
            while (i + ulim - 1 < (int)MN.size() && i + ulim - 1 < (int)M) {
                if (b_disp)
                    cout << (MN[i - 1] - MN[i + ulim - 1]) << " "
                         << MN[i + ulim - 1] << endl;

                if ((MN[i - 1] - MN[i + ulim - 1]) < MN[i + ulim - 1]
                     && MN[i + ulim - 1] < 600000000) {
                    mlim = i - 1;
                    break;
                }
                ++i;
            }
            break;
        }
    }

    if (b_disp)
        cout << "M is: " << M << " Mlim is: " << mlim
             << " ulim is: " << ulim
             << " original mlim is: " << orgmlim
             << " guess is: "
             << round((log(N) - log(6)) / log(real_L)) << endl;

    if (mlim < (int)M) {
        for (int i = 0; i < real_L; ++i)
            VDFS.emplace_back(i);
    }

    L = static_cast<unsigned int>(real_L);
    N = 0;
    M = 0;
    return true;
}


// ─────────────────────────────────────────────────────────────────────────────
// Load_items_pre
// ─────────────────────────────────────────────────────────────────────────────
bool Load_items_pre(string &inst_name) {
    ifstream file(inst_name);
    if (!file.good()) {
        if (b_disp)
            cout << "!!!!!! No such file exists: " << inst_name << " !!!!!!\n";
        return false;
    }

    string line;
    int ditem;
    while (getline(file, line) && give_time(clock() - start_time) < time_limit) {
        istringstream word(line);
        string itm;
        vector<int> temp_vec;
        vector<int> temp_lim;
        bool sgn = false;

        while (word >> itm) {
            ditem = stoi(itm);
            if (item_dic[std::abs(ditem) - 1] == -1) {
                if (!sgn)
                    sgn = (ditem < 0);
                continue;
            } else {
                if (ditem > 0)
                    ditem = item_dic[ditem - 1];
                else
                    ditem = -item_dic[-ditem - 1];
            }
            if (sgn) {
                if (ditem > 0)
                    ditem = -ditem;
                sgn = false;
            }
            if (temp_vec.size() <= (size_t)mlim)
                temp_vec.push_back(ditem);
            else
                temp_lim.push_back(ditem);
        }

        if (temp_vec.empty())
            continue;

        ++N;
        if (b_disp && N % 10000000 == 0)
            cout << N << endl;

        if (temp_vec.size() + temp_lim.size() > (size_t)M)
            M = static_cast<unsigned int>(temp_vec.size() + temp_lim.size());

        while (DFS.size() < L)
            DFS.emplace_back(-static_cast<int>(DFS.size()) - 1);
        while (VDFS.size() < L)
            VDFS.emplace_back(static_cast<int>(VDFS.size()));

        Build_MDD(temp_vec, temp_lim);
    }

    return true;
}


// ─────────────────────────────────────────────────────────────────────────────
// Load_items (no preprocess)
// ─────────────────────────────────────────────────────────────────────────────
bool Load_items(string &inst_name) {
    ifstream file(inst_name);
    if (!file.good()) {
        if (b_disp)
            cout << "!!!!!! No such file exists: " << inst_name << " !!!!!!\n";
        return false;
    }

    string line;
    int ditem;
    while (getline(file, line) && give_time(clock() - start_time) < time_limit) {
        ++N;
        if (b_disp && N % 1000000 == 0)
            cout << "Found " << N << " sequence, with max line len "
                 << M << ", and " << L << " items, and " << E
                 << " enteries\n";

        istringstream word(line);
        string itm;
        vector<int> temp_vec;
        vector<int> temp_lim;

        while (word >> itm) {
            ditem = stoi(itm);

            if (ditem > 0)
                itmset_exists = true;

            if (L < static_cast<unsigned int>(std::abs(ditem))) {
                L = static_cast<unsigned int>(std::abs(ditem));

                while (DFS.size() < L)
                    DFS.emplace_back(-static_cast<int>(DFS.size()) - 1);
                while (VDFS.size() < L)
                    VDFS.emplace_back(static_cast<int>(VDFS.size()));
            }

            if (temp_vec.size() < (size_t)mlim)
                temp_vec.push_back(ditem);
            else
                temp_lim.push_back(ditem);
        }
        E += static_cast<unsigned long long>(temp_vec.size() + temp_lim.size());
        if (temp_vec.size() + temp_lim.size() > (size_t)M)
            M = static_cast<unsigned int>(temp_vec.size() + temp_lim.size());

        while (DFS.size() < L)
            DFS.emplace_back(-static_cast<int>(DFS.size()) - 1);
        while (VDFS.size() < L)
            VDFS.emplace_back(static_cast<int>(VDFS.size()));

        Build_MDD(temp_vec, temp_lim);
    }

    return true;
}

} // namespace largehm
