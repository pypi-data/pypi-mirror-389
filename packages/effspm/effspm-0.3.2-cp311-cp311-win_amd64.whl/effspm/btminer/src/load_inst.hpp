#pragma once

#include <vector>
#include <string>
#include <fstream>
#include <map>
#include <unordered_set>
#include <unordered_map>
#include <ctime>

namespace btminer {

using std::string;
using std::vector;
using std::map;
using std::unordered_map;
using std::unordered_set;

bool Load_instance(string& items_file, double thresh);

extern string out_file, folder;

extern bool b_disp, b_write, use_dic, just_build, pre_pro;

extern int  N, M, L, theta, num_nodes, M_mult, N_mult, time_limit, cur_node;
extern unsigned long long E;              // total number of entries (we need this for _effspm.cpp)

extern std::clock_t start_time;

// these 2 are for dictionary mode
extern map<string,int> item_map;
extern map<int,string> item_map_rev;

extern vector<int> freq;
extern vector<int> item_dic;

// expose items so _effspm.cpp can fall back to seeding (it expects btminer::items)
extern vector<vector<int>> items;

class Pattern;
extern vector<Pattern> DFS;

} // namespace btminer
