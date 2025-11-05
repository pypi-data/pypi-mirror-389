#include "utility.hpp"
#include <iostream>
#include <fstream>

// timing
std::clock_t start_time;

// flags
bool b_disp = false, b_write = false, use_dic = false, use_list = false, pre_pro = false;
unsigned int time_limit = 10 * 3600;
std::string out_file;

// storage for Python
static std::vector<std::vector<int>> collected_patterns;

double give_time(std::clock_t end_time) {
    return static_cast<double>(end_time) / CLOCKS_PER_SEC;
}

void ClearCollected() {
    collected_patterns.clear();
}

const std::vector<std::vector<int>>& GetCollected() {
    return collected_patterns;
}

// collect for Python
void CollectPattern(const std::vector<int>& seq) {
    collected_patterns.push_back(seq);
}

// non-const overload forwards to const version
void Out_patt(std::vector<int>& seq, unsigned int freq) {
    Out_patt(static_cast<const std::vector<int>&>(seq), freq);
}

// actual implementation
void Out_patt(const std::vector<int>& seq, unsigned int freq) {
    // 1) collect for Python
    CollectPattern(seq);

    // 2) optional console output
    if (b_disp) {
        for (int x : seq) std::cout << x << ' ';
        std::cout << "\n************** Freq: " << freq << "\n";
    }

    // 3) optional file output
    if (b_write) {
        std::ofstream ofs(out_file, std::ios::app);
        for (int x : seq) ofs << x << ' ';
        ofs << "\n************** Freq: " << freq << "\n";
    }
}
