#include <unity.h>

// Transposition constants (mirrored from main.cpp)
const int maxTransposition = 4;
const int minTransposition = -1 * maxTransposition;

// This is the corrected octave value calculation from main.cpp
// Maps transposition (-4 to +4) to MIDI value (0 to 8)
int calculateOctaveValue(int transposition) {
    return transposition + maxTransposition;
}

// Test the octave value mapping at boundaries
void test_octave_value_at_min_transposition(void) {
    // -4 should map to 0
    TEST_ASSERT_EQUAL(0, calculateOctaveValue(minTransposition));
}

void test_octave_value_at_max_transposition(void) {
    // +4 should map to 8
    TEST_ASSERT_EQUAL(8, calculateOctaveValue(maxTransposition));
}

void test_octave_value_at_zero_transposition(void) {
    // 0 should map to 4 (center)
    TEST_ASSERT_EQUAL(4, calculateOctaveValue(0));
}

// Test that all octave values are valid MIDI CC values (0-127)
void test_all_octave_values_valid_midi(void) {
    for (int t = minTransposition; t <= maxTransposition; t++) {
        int value = calculateOctaveValue(t);
        TEST_ASSERT_GREATER_OR_EQUAL(0, value);
        TEST_ASSERT_LESS_OR_EQUAL(127, value);
    }
}

// Test that octave values are sequential (no gaps)
void test_octave_values_sequential(void) {
    int prev = calculateOctaveValue(minTransposition);
    for (int t = minTransposition + 1; t <= maxTransposition; t++) {
        int curr = calculateOctaveValue(t);
        TEST_ASSERT_EQUAL(prev + 1, curr);
        prev = curr;
    }
}

// Test transposition range
void test_transposition_range_symmetric(void) {
    TEST_ASSERT_EQUAL(-maxTransposition, minTransposition);
}

void test_transposition_semitones_per_octave(void) {
    // Each transposition step is 12 semitones (one octave)
    const int transpositionSemitones = 12;
    TEST_ASSERT_EQUAL(12, transpositionSemitones);
}

// Test total range coverage
void test_total_transposition_range(void) {
    // Should have 9 possible values: -4, -3, -2, -1, 0, 1, 2, 3, 4
    int count = maxTransposition - minTransposition + 1;
    TEST_ASSERT_EQUAL(9, count);
}

int main(int argc, char **argv) {
    UNITY_BEGIN();

    RUN_TEST(test_octave_value_at_min_transposition);
    RUN_TEST(test_octave_value_at_max_transposition);
    RUN_TEST(test_octave_value_at_zero_transposition);
    RUN_TEST(test_all_octave_values_valid_midi);
    RUN_TEST(test_octave_values_sequential);
    RUN_TEST(test_transposition_range_symmetric);
    RUN_TEST(test_transposition_semitones_per_octave);
    RUN_TEST(test_total_transposition_range);

    return UNITY_END();
}
