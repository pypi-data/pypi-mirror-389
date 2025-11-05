#pragma once

#include <vector>
#include <string>
#include <fstream>
#include <map>
#include <unordered_set>
#include <unordered_map>
#include <time.h>

namespace htminer {

using std::string;
using std::vector;

bool Load_instance(string& items_file, double thresh);

extern string out_file, folder;

extern bool b_disp;
extern bool b_write;
extern bool use_dic;
extern bool just_build;
extern bool pre_pro;
extern bool itmset_exists;

extern unsigned int        M;
extern unsigned int        mlim;
extern unsigned int        time_limit;
extern unsigned long long  N;
extern unsigned long long  L;
extern unsigned long long  theta;
extern unsigned long long  E;

// 🔥 This is the missing declaration that fixes the error:
extern vector<int> item_dic;

extern clock_t start_time;

} // namespace htminer
