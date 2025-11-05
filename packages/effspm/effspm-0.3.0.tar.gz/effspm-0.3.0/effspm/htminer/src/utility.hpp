#pragma once

#include <vector>
#include <ctime>
#include <string>
#include "build_mdd.hpp"
#include "freq_miner.hpp"
#include "load_inst.hpp"

namespace htminer {

// ─── Global flags and counters ─────────────────────────────────────────────
/// Controls whether to mine in “list” mode (unused for HTMiner, but declared)
extern bool use_list;
/// If true, only build MDD and exit (don’t actually mine)
extern bool just_build;
/// If true, print each pattern to stdout as it’s found
extern bool b_disp;
/// If true, write each pattern to file (see out_file)
extern bool b_write;
/// If true, use a dictionary‐file mapping items → new IDs
extern bool use_dic;
/// If true, preprocess input (create dictionary) instead of mining
extern bool pre_pro;

/// Time limit (in seconds) for mining before forced exit
extern unsigned int time_limit;
/// Output filename (if b_write is true)
extern std::string out_file;
/// Clock tick when mining started
extern std::clock_t start_time;

// ─── Data‐set‐level globals ─────────────────────────────────────────────────
/// The input sequences (each sequence is a vector of integers)
extern std::vector<std::vector<int>> items;
/// Number of sequences (items.size())
extern unsigned long long N;
/// Number of distinct items (max absolute item ID)
extern unsigned long long L;
/// Minimum support threshold (absolute count, not fraction)
extern unsigned long long theta;
/// Maximum sequence length across all items
extern unsigned int M;
/// Total number of “entries” (sum of all sequence lengths)
extern unsigned long long E;

// ─── Per‐pattern DFS stacks ─────────────────────────────────────────────────
/// DFS stack of “in‐memory” patterns (each Pattern holds its own ilist/slist, freq, str_pnt, etc.)
extern std::vector<Pattern> DFS;

extern std::vector<std::vector<int>> collectedPatterns;
// ─── Collected output ───────────────────────────────────────────────────────
/// Clears any patterns left in DFS (called at the start of each run)
inline void ClearCollected() {
    DFS.clear();
    collectedPatterns.clear();     
}
/// Returns a reference to the entire “collected patterns” vector
/// (each Pattern knows how to output itself as a vector<int>)
const std::vector<std::vector<int>>& GetCollected();

// ─── Helper functions ───────────────────────────────────────────────────────
/// Given a clock‐tick difference, return elapsed seconds as a float
float give_time(std::clock_t kk);

/// Check whether a candidate can extend its parent pattern:
///   cur_arc  = current Arc node ID in MDD
///   str_pnt  = string‐pointer of the existing pattern
///   start    = starting index within the MDD arc‐list
///   strpnt_vec = parent’s “string pointers” vector
/// Returns true if `cur_arc` is a valid child of `str_pnt` from position `start`.
bool check_parent(unsigned int cur_arc,
                  unsigned int str_pnt,
                  unsigned int start,
                  std::vector<unsigned int>& strpnt_vec);

} // namespace htminer
