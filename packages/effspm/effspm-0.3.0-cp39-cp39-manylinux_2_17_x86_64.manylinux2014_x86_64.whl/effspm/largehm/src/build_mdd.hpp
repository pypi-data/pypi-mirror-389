#ifndef LARGEHM_BUILD_MDD_HPP
#define LARGEHM_BUILD_MDD_HPP

#include <vector>
#include <unordered_map>
#include <cstddef>          // for size_t
#include <cstdint>          // for uint64_t

#include "load_inst.hpp"    // defines L, DFS, VDFS, Tree, etc.
#include "freq_miner.hpp"   // for Pattern, VPattern
#include "utility.hpp"      // if you need check_parent or collected

namespace largehm {

//
// ─── Types & Globals ─────────────────────────────────────────────────────────
//

struct Arc;
struct VArc;
struct CArc;

extern std::vector<Arc>       Tree;
extern std::vector<VArc>      VTree;
extern std::vector<CArc>      CTree;

//
// ─── Public API ───────────────────────────────────────────────────────────────
//

void Build_MDD(std::vector<int>& items,
               std::vector<int>& items_lim);

//
// ─── Internal Helpers ─────────────────────────────────────────────────────────
//

int Add_arc(int item,
            std::uint64_t last_arc,
            int& itmset,
            std::unordered_map<int, std::uint64_t>& ancest_map);

void Add_vec(std::vector<int>& items_lim,
             std::unordered_map<int, std::uint64_t>& ancest_map,
             std::uint64_t last_arc,
             int itmset);

//
// ─── Struct Definitions ───────────────────────────────────────────────────────
//

struct Arc {
    int                item;
    int                itmset;
    std::uint64_t      anct;
    std::uint64_t      chld;
    std::uint64_t      sibl;
    unsigned long long freq;

    Arc(int _item, int _itmset, std::uint64_t _anct)
      : item(_item), itmset(_itmset), anct(_anct),
        chld(0), sibl(0), freq(0u) {}
};

struct VArc {
    std::vector<int>            seq;
    std::uint64_t               sibl;
    unsigned long long          freq;

    explicit VArc(std::vector<int>& items, std::uint64_t _sibl)
      : seq(), sibl(_sibl), freq(0u)
    {
        seq.swap(items);
    }
};

struct CArc {
    std::vector<std::uint64_t>  ancest;
    std::vector<int>            seq;
    unsigned long long          freq;

    explicit CArc(std::vector<std::uint64_t>& _anc,
                  std::vector<int>& items)
      : ancest(), seq(), freq(0u)
    {
        ancest.swap(_anc);
        seq.swap(items);
    }
};

} // namespace largehm

#endif // LARGEHM_BUILD_MDD_HPP
