#pragma once
#include <vector>
#include <cstdint>

namespace largebm {

class Arc {
public:
    unsigned long long chld = 0;
    unsigned long long sibl = 0;
    unsigned long long freq = 0;
    unsigned long long anct = 0;
    int itmset = 0;
    int item = 0;

    Arc() = default;
    Arc(int _itm, int _itmset, unsigned long long _anc)
        : chld(0), sibl(0), freq(0), anct(_anc), itmset(_itmset), item(_itm) {}
    Arc(int _itm, unsigned long long _anc)
        : chld(0), sibl(0), freq(0), anct(_anc), item(_itm) {}
};

// Single global MDD, defined in build_mdd.cpp
extern std::vector<Arc> Tree;

// [2025-10-25 NEW]: const-correct signature used everywhere
void Build_MDD(const std::vector<int>& items);

// [2025-10-25 NEW]: debug helper to read how many anct==0 ticks we did
unsigned long long _effspm_dbg_anct0_ticks();

} // namespace largebm
