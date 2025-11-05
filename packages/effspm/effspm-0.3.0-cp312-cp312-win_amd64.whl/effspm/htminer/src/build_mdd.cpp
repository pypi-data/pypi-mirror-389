#include <vector>
#include <iostream>
#include "load_inst.hpp"
#include "build_mdd.hpp"
#include "freq_miner.hpp"
#include "utility.hpp"

namespace htminer {

// Forward declarations (unchanged)
int Add_arc(int item, unsigned int last_arc, int& itmset, std::vector<unsigned int>& ancest_map);
void Add_vec(std::vector<int>& items_lim, std::vector<unsigned int>& ancest_map, unsigned int last_arc, int itmset);

// Global trees (unchanged)
std::vector<Arc>  Tree;
std::vector<VArc> VTree;
std::vector<CArc> CTree;

void Build_MDD(std::vector<int>& items, std::vector<int>& items_lim) {
    // Prepare ancestor map of size L
    std::vector<unsigned int> ancest_map(L, 0);

    unsigned int last_arc = 0;
    int          itmset   = 0;

    // 1) normal items
    for (size_t idx = 0; idx < items.size(); ++idx) {
        int curr_item = items[idx];

        ++E;   // ✅ count this entry, just like in btminer

        last_arc = Add_arc(curr_item, last_arc, itmset, ancest_map);
    }

    // 2) tail / limited items
    if (!items_lim.empty()) {
        Add_vec(items_lim, ancest_map, last_arc, itmset);
    }
}

int Add_arc(int item,
            unsigned int last_arc,
            int& itmset,
            std::vector<unsigned int>& ancest_map)
{
    unsigned int anct = ancest_map[std::abs(item) - 1];
    if (item < 0)
        ++itmset;

    unsigned int last_sibl = Tree[last_arc].chld;

    if (last_sibl == 0) {
        Tree.emplace_back(item, itmset, anct);
        last_sibl = static_cast<unsigned int>(Tree.size() - 1);
        Tree[last_arc].chld = last_sibl;

        if (anct == 0)
            DFS[std::abs(item) - 1].str_pnt.push_back(last_sibl);
    }
    else {
        while (Tree[last_sibl].item != item) {
            if (Tree[last_sibl].sibl == 0) {
                Tree.emplace_back(item, itmset, anct);
                Tree[last_sibl].sibl = static_cast<unsigned int>(Tree.size() - 1);
                last_sibl            = static_cast<unsigned int>(Tree.size() - 1);
                if (anct == 0)
                    DFS[std::abs(item) - 1].str_pnt.push_back(last_sibl);
                break;
            }
            last_sibl = Tree[last_sibl].sibl;
        }
    }

    if (anct == 0)
        ++DFS[std::abs(item) - 1].freq;

    ++Tree[last_sibl].freq;

    ancest_map[std::abs(item) - 1] = last_sibl;

    return static_cast<int>(last_sibl);
}

void Add_vec(std::vector<int>& items_lim,
             std::vector<unsigned int>& ancest,
             unsigned int last_arc,
             int itmset)
{
    items_lim.shrink_to_fit();

    std::vector<bool> counted(L, false);

    if (Tree[last_arc].itmset > 0) {
        ancest.push_back(0);
        ancest.shrink_to_fit();

        for (size_t i = 0; i < items_lim.size(); ++i) {
            int cur_itm = std::abs(items_lim[i]);

            ++E;   // ✅ count this limited-entry too

            if (ancest[cur_itm - 1] == 0 && !counted[cur_itm - 1]) {
                if (i + 1 < static_cast<int>(items_lim.size())) {
                    VDFS[cur_itm - 1].str_pnt.push_back(-static_cast<int>(i) - 1);
                    VDFS[cur_itm - 1].seq_ID.push_back(static_cast<unsigned int>(CTree.size()));
                }
                ++DFS[cur_itm - 1].freq;
                counted[cur_itm - 1] = true;
            }
        }

        CTree.emplace_back(ancest, items_lim);
        Tree[last_arc].chld   = static_cast<unsigned int>(CTree.size() - 1);
        Tree[last_arc].itmset = -itmset;
    }
    else {
        std::vector<unsigned int>& ancest_ct = CTree[Tree[last_arc].chld].ancest;

        for (size_t i = 0; i < items_lim.size(); ++i) {
            int cur_itm = std::abs(items_lim[i]);

            ++E;   // ✅ also count in this branch

            if (!counted[cur_itm - 1] && ancest_ct[cur_itm - 1] == 0) {
                if (i + 1 < static_cast<int>(items_lim.size())) {
                    VDFS[cur_itm - 1].str_pnt.push_back(static_cast<unsigned int>(i) + 1);
                    VDFS[cur_itm - 1].seq_ID.push_back(static_cast<unsigned int>(VTree.size()));
                }
                ++DFS[cur_itm - 1].freq;
                counted[cur_itm - 1] = true;
            }
        }

        VTree.emplace_back(items_lim, ancest_ct.back());
        CTree[Tree[last_arc].chld].ancest.back() = static_cast<unsigned int>(VTree.size());
    }
}

} // namespace htminer
