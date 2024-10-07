#include <map>
#include <bitset>

#include "msl/fwcounter.h"
#include "ooo_cpu.h"


namespace
{
constexpr std::size_t BIMODAL_TABLE_SIZE = 16384;
constexpr std::size_t COUNTER_BITS = 2;
constexpr std::size_t HISTORIES_TABLE_DEPTH = 14;

std::bitset<HISTORIES_TABLE_DEPTH> History {"00000000000000"};


std::map<O3_CPU*, std::array<champsim::msl::fwcounter<COUNTER_BITS>, BIMODAL_TABLE_SIZE>> bimodal_table;
// std::map<O3_CPU*, std::array<std::bitset<HISTORIES_TABLE_DEPTH>,BIMODAL_TABLE_SIZE>> history_table;

} // namespace

void O3_CPU::initialize_branch_predictor() {}

uint8_t O3_CPU::predict_branch(uint64_t ip)
{
    auto value = ::bimodal_table[this][History.to_ullong()]; // 
    // printf("%d", value.to_ullong());
    return value.value()>= 2;
}

void O3_CPU::last_branch_result(uint64_t ip, uint64_t branch_target, uint8_t taken, uint8_t branch_type)
{
  // This code updates the table based on the previous result
  
  ::bimodal_table[this][History.to_ullong()] += taken ? 1 : -1; // If the value for that has was taken, then we increment our value in the table by 1, else subtract 1 
  // Update the history bitset with the most recent data 
  History >>= 1;
  History[HISTORIES_TABLE_DEPTH-1] = taken;
  // printf("History:%b \n" , History);
}
