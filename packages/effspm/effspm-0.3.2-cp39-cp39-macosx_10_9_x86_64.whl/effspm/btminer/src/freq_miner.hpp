#pragma once

#include <vector>
#include "load_inst.hpp"
#include "build_mdd.hpp"

namespace btminer {

void Freq_miner();

/**
 * One pattern in the DFS stack.
 * (same as professor)
 */
class Pattern {
public:
    std::vector<int> seq;
    std::vector<int> str_pnt;
    std::vector<int> slist;
    std::vector<int> ilist;
    int freq;

    Pattern(std::vector<int>& _seq, int item) {
        seq.swap(_seq);
        seq.push_back(item);
        freq = 0;
    }

    Pattern(int item) {
        seq.push_back(item);
        freq = 0;
    }

    Pattern() {
        freq = 0;
    }
};

// ----- existing globals -----
extern int num_patt;
extern int num_max_patt;
extern std::vector<Pattern> DFS;

// ----- NEW: collected patterns for Python binding -----

// stores every pattern exactly as mined: [-68, -36, -5, ...]
extern std::vector<std::vector<int>> collectedPatterns;

// clear before every run
void ClearCollected();

// read-only access (Python binding will use this)
const std::vector<std::vector<int>>& GetCollected();

} // namespace btminer
