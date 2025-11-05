// ─── effspm/largehm/src/build_mdd.cpp ─────────────────────────────────────────

#include "build_mdd.hpp"

// ─── Definitions of the extern globals declared in build_mdd.hpp ─────────────
std::vector<largehm::Arc>       largehm::Tree;
std::vector<largehm::VArc>      largehm::VTree;
std::vector<largehm::CArc>      largehm::CTree;

#include <vector>
#include <iostream>
#include <cmath>           // for std::abs
#include <unordered_map>
#include <cstdint>         // for std::uint64_t
#include "load_inst.hpp"
#include "freq_miner.hpp"
#include "utility.hpp"

namespace largehm {

//
// ─── Build the MDD by sequentially calling Add_arc() then possibly Add_vec() ──
//
void Build_MDD(std::vector<int>& items, std::vector<int>& items_lim) {
    // SANITY CHECK: show sizes before building
    
    std::unordered_map<int, std::uint64_t> ancest_map;
    std::uint64_t last_arc = 0;
    int itmset = 0;

    // Insert each prefix item as an arc
    for (auto it = items.begin(); it != items.end(); ++it) {
        last_arc = Add_arc(*it, last_arc, itmset, ancest_map);
    }

    // If there is a suffix beyond mlim, attach it via Add_vec()
    if (!items_lim.empty()) {
        Add_vec(items_lim, ancest_map, last_arc, itmset);
    }
}


//
// ─── Add_arc: insert a single “item” into the MDD under parent last_arc. ──────
//
int Add_arc(int item,
            std::uint64_t last_arc,
            int& itmset,
            std::unordered_map<int, std::uint64_t>& ancest_map)
{
    // Ensure DFS is at least size |item|
    size_t needed = static_cast<size_t>(std::abs(item));
    if (DFS.size() < needed) {
        size_t old = DFS.size();
        DFS.resize(needed);
        for (size_t i = old; i < needed; ++i) {
            DFS[i] = Pattern(-static_cast<int>(i) - 1);
        }
    }

    unsigned int anct = 0;
    auto p = ancest_map.find(std::abs(item));
    if (p != ancest_map.end()) {
        anct = p->second;
    }

    if (item < 0) {
        ++itmset;
    }

    std::uint64_t last_sibl = Tree[last_arc].chld;
    if (last_sibl == 0) {
        // No child yet: create a new Arc
        Tree.emplace_back(item, itmset, anct);
        last_sibl = Tree.size() - 1;
        Tree[last_arc].chld = last_sibl;
        if (anct == 0) {
            DFS[std::abs(item) - 1].str_pnt.push_back(last_sibl);
        }
    }
    else {
        // Traverse siblings until we find a match or append
        while (Tree[last_sibl].item != item) {
            if (Tree[last_sibl].sibl == 0) {
                Tree.emplace_back(item, itmset, anct);
                Tree[last_sibl].sibl = Tree.size() - 1;
                last_sibl = Tree.size() - 1;
                if (anct == 0) {
                    DFS[std::abs(item) - 1].str_pnt.push_back(last_sibl);
                }
                break;
            }
            last_sibl = Tree[last_sibl].sibl;
        }
    }

    if (anct == 0) {
        ++DFS[std::abs(item) - 1].freq;
    }
    ++Tree[last_sibl].freq;
    ancest_map[std::abs(item)] = last_sibl;
    return static_cast<int>(last_sibl);
}


//
// ─── Add_vec: attach the “items_lim” vector as children/vertical arcs ─────────
//
void Add_vec(std::vector<int>& items_lim,
             std::unordered_map<int, std::uint64_t>& ancest_map,
             std::uint64_t last_arc,
             int itmset)
{
    // Ensure VDFS and DFS are at least size L
    if (VDFS.size() < static_cast<size_t>(L)) {
        size_t old = VDFS.size();
        VDFS.resize(static_cast<size_t>(L));
        for (size_t i = old; i < VDFS.size(); ++i) {
            VDFS[i] = VPattern(static_cast<int>(i));
        }
    }
    if (DFS.size() < static_cast<size_t>(L)) {
        size_t old = DFS.size();
        DFS.resize(static_cast<size_t>(L));
        for (size_t i = old; i < DFS.size(); ++i) {
            DFS[i] = Pattern(-static_cast<int>(i) - 1);
        }
    }

    items_lim.shrink_to_fit();
    std::vector<bool> counted(L, false);

    // If this node has positive itmset (>0) or no CTree child yet, create first child entry
    if (Tree[last_arc].itmset > 0 || Tree[last_arc].chld == 0) {
        std::vector<std::uint64_t> ancest(L + 1, 0ULL);
        for (auto& kv : ancest_map) {
            ancest[kv.first - 1] = kv.second;
            counted[kv.first - 1] = true;
        }
        for (int i = 0; i < static_cast<int>(items_lim.size()); ++i) {
            int cur_itm = std::abs(items_lim[i]);
            if (!counted[cur_itm - 1]) {
                if (i + 1 < static_cast<int>(items_lim.size())) {
                    VDFS[cur_itm - 1].str_pnt.push_back(-i - 1);
                    VDFS[cur_itm - 1].seq_ID.push_back(CTree.size());
                }
                ++DFS[cur_itm - 1].freq;
                counted[cur_itm - 1] = true;
            }
        }
        CTree.emplace_back(ancest, items_lim);
        Tree[last_arc].chld  = CTree.size() - 1;
        Tree[last_arc].itmset = -itmset;
    }
    else {
        // Normal “existing CTree child” path
        auto& ancest = CTree[ Tree[last_arc].chld ].ancest;
        for (int i = 0; i < static_cast<int>(items_lim.size()); ++i) {
            int cur_itm = std::abs(items_lim[i]);
            if (!counted[cur_itm - 1] && ancest[cur_itm - 1] == 0ULL) {
                if (i + 1 < static_cast<int>(items_lim.size())) {
                    VDFS[cur_itm - 1].str_pnt.push_back(i + 1);
                    VDFS[cur_itm - 1].seq_ID.push_back(VTree.size());
                }
                ++DFS[cur_itm - 1].freq;
                counted[cur_itm - 1] = true;
            }
        }
        VTree.emplace_back(items_lim, CTree[ Tree[last_arc].chld ].ancest.back());
        CTree[ Tree[last_arc].chld ].ancest.back() = VTree.size();
    }
}

} // namespace largehm
