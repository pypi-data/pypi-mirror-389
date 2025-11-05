#ifndef LARGEHM_FREQ_MINER_HPP
#define LARGEHM_FREQ_MINER_HPP
#include <cstdint>
#include <vector>
#include <string>
#include <fstream>
#include <ctime>      // for clock_t
extern std::vector<std::uint64_t> ancest_base;
namespace largehm {

//
// ─── Pattern & VPattern ──────────────────────────────────────────────────────
//

class Pattern {
public:
    std::vector<int>            seq;
    unsigned int                freq;
    std::vector<int>            list;
    std::vector<unsigned long long int> str_pnt;

    Pattern(int start_code = 0) : freq(0) {
        if (start_code != 0)
            seq.push_back(start_code);
    }
};

class VPattern {
public:
    std::vector<unsigned long long int> str_pnt;
    std::vector<unsigned long long int> seq_ID;
    int                                 ass_patt;

    VPattern(int assoc = -1) : ass_patt(assoc) {}
};

//
// ─── Globals used by Freq_miner ──────────────────────────────────────────────
//
extern std::vector<Pattern>    DFS;
extern std::vector<VPattern>   VDFS;

extern unsigned long long int num_patt;

extern std::vector<bool>       ilist;
extern std::vector<bool>       slist;

extern std::vector<Pattern>    pot_patt;
extern std::vector<VPattern>   pot_vpatt;
extern std::vector<unsigned long long int> last_strpnt;

extern std::vector<int>       DFS_numfound;

extern Pattern                 _patt;
extern VPattern                _vpatt;

extern int                     itmset_size;
extern int                     last_neg;
extern bool                    ilist_nempty;

//
// ─── Function Prototypes ─────────────────────────────────────────────────────
//
void Freq_miner();
void Extend_patt(Pattern& _patt);
void Mine_vec(std::uint64_t seq_ID,
              int pos,
              int num_found,
              std::vector<std::uint64_t>& ancest,
              std::vector<int>& items,
              std::uint64_t pnt,
              int sgn);
void Out_patt(std::vector<int>& seq, unsigned int freq);

} // namespace largehm

#endif // LARGEHM_FREQ_MINER_HPP
