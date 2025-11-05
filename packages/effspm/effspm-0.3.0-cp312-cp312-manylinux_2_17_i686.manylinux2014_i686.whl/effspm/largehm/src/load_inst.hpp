#ifndef LARGEHM_LOAD_INST_HPP
#define LARGEHM_LOAD_INST_HPP

#include <string>
#include <vector>
#include <fstream>
#include <ctime>     // for clock_t

// We need Pattern and VPattern, so include freq_miner.hpp here:
#include "freq_miner.hpp"

namespace largehm {

//
// ─── Globals & Function Prototypes ───────────────────────────────────────────
//

// Output/folder:
extern std::string out_file;
extern std::string folder;

// Flags:
extern bool b_disp;
extern bool b_write;
extern bool use_dic;
extern bool use_list;
extern bool just_build;
extern bool pre_pro;
extern bool itmset_exists;

// Database statistics:
extern unsigned int M;
extern unsigned int L;
extern unsigned int mlim;
extern unsigned int time_limit;

extern unsigned long long int N;
extern unsigned long long int theta;
extern unsigned long long int E;

// Timing:
extern clock_t start_time;

// In‐memory sequences (only if “in‐memory” mode):
extern std::vector<std::vector<int>> items;

// Preprocessing dictionary (maps original → compressed IDs):
extern std::vector<int> item_dic;

// DFS stacks used by the miner (Pattern / VPattern):
extern std::vector<Pattern>   DFS;
extern std::vector<VPattern>  VDFS;

// Internal loader functions:
bool Load_items_pre(std::string &inst_name);
bool Load_items(std::string &inst_name);
bool Preprocess(std::string &inst, double thresh);

// Main entry‐point for loading & building the MDD:
bool Load_instance(std::string &items_file, double thresh);

} // namespace largehm

#endif // LARGEHM_LOAD_INST_HPP
