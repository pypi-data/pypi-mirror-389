#pragma once
#include <vector>
#include "load_inst.hpp"
#include <cstdlib> 
#include <cmath> 
#include <cstddef>  // for std::size_t

using namespace std;
void Freq_miner();
void Out_patt(std::vector<int>& seq, unsigned int freq);


class Pattern {
public:

	vector<int> seq;
	vector<unsigned int> str_pnt;
	vector<unsigned int> seq_ID;

	vector<int> slist;
	vector<int> ilist;

	unsigned int freq;

	Pattern(vector<int>& _seq, int item) {
		seq.reserve(_seq.size());
		for (int i = 0; i < _seq.size(); ++i)


			seq.push_back(_seq[i]);
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

extern vector<Pattern> DFS;				//DFS queue of potential patterns to extend

extern unsigned long long int num_patt;
