#ifndef UTILITY_HPP
#define UTILITY_HPP

#include <vector>
#include <string>
#include <ctime>

// timing
extern std::clock_t start_time;
double give_time(std::clock_t end_time);

// flags (shared with main.cpp)
extern bool b_disp, b_write, use_dic, use_list, pre_pro;
extern unsigned int time_limit;
extern std::string out_file;

// Python-binding collection
void ClearCollected();
const std::vector<std::vector<int>>& GetCollected();

// pattern collection & output
void CollectPattern(const std::vector<int>& seq);

// two overloads of Out_patt so calls with non‑const or const vectors both link
void Out_patt(std::vector<int>& seq, unsigned int freq);
void Out_patt(const std::vector<int>& seq, unsigned int freq);

#endif // UTILITY_HPP

