// effspm/load_inst.hpp
#pragma once

#include <vector>
#include <string>
#include <fstream>
#include <map>
#include <ctime>    // for clock_t

using namespace std;

// ------------------------------------------------------------
// forward declare Pattern (defined in freq_miner.hpp)
struct Pattern;


// Main entrypoint: load your file on disk into 'items', build DFS, theta, etc.
bool Load_instance(string &items_file, double thresh);

// storage & globals shared between the C++-CLI & Python bindings
extern vector<vector<int>> items;
extern vector<Pattern>     DFS;         // now Pattern is known
extern vector<int>         item_dic;

extern string              out_file;
extern bool                b_disp, b_write, use_dic, use_list, pre_pro;

extern unsigned int        M, L, time_limit;
extern unsigned long long  N, E, theta; // E = total number of entries

extern clock_t             start_time;
