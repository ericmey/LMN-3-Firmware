#include <unity.h>
#include <set>

// Mock Arduino.h is included via -I test/mocks build flag
// This allows config.h's #include <Arduino.h> to find our mock
#include "../../src/config.h"

// MIDI CC values must be in range 0-127
void test_cc_values_in_valid_midi_range(void) {
    TEST_ASSERT_LESS_OR_EQUAL(127, ENCODER_1);
    TEST_ASSERT_LESS_OR_EQUAL(127, ENCODER_2);
    TEST_ASSERT_LESS_OR_EQUAL(127, ENCODER_3);
    TEST_ASSERT_LESS_OR_EQUAL(127, ENCODER_4);
    TEST_ASSERT_LESS_OR_EQUAL(127, ENCODER_1_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, ENCODER_2_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, ENCODER_3_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, ENCODER_4_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, UNDO_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, TEMPO_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, SAVE_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, SETTINGS_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, TRACKS_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, MIXER_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, PLUGINS_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, MODIFIERS_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, SEQUENCERS_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, LOOP_IN_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, LOOP_OUT_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, LOOP_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, CUT_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, PASTE_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, SLICE_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, RECORD_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, PLAY_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, STOP_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, CONTROL_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, OCTAVE_CHANGE);
    TEST_ASSERT_LESS_OR_EQUAL(127, PLUS_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, MINUS_BUTTON);
    TEST_ASSERT_LESS_OR_EQUAL(127, DUMMY);
}

// CC values should be non-negative
void test_cc_values_non_negative(void) {
    TEST_ASSERT_GREATER_OR_EQUAL(0, ENCODER_1);
    TEST_ASSERT_GREATER_OR_EQUAL(0, ENCODER_2);
    TEST_ASSERT_GREATER_OR_EQUAL(0, ENCODER_3);
    TEST_ASSERT_GREATER_OR_EQUAL(0, ENCODER_4);
    TEST_ASSERT_GREATER_OR_EQUAL(0, DUMMY);
}

// Row pins should all be unique
void test_row_pins_unique(void) {
    std::set<int> pins;
    pins.insert(ROW_0);
    pins.insert(ROW_1);
    pins.insert(ROW_2);
    pins.insert(ROW_3);
    pins.insert(ROW_4);
    TEST_ASSERT_EQUAL(5, pins.size());
}

// Column pins should all be unique
void test_col_pins_unique(void) {
    std::set<int> pins;
    pins.insert(COL_0);
    pins.insert(COL_1);
    pins.insert(COL_2);
    pins.insert(COL_3);
    pins.insert(COL_4);
    pins.insert(COL_5);
    pins.insert(COL_6);
    pins.insert(COL_7);
    pins.insert(COL_8);
    pins.insert(COL_9);
    pins.insert(COL_10);
    pins.insert(COL_11);
    pins.insert(COL_12);
    pins.insert(COL_13);
    TEST_ASSERT_EQUAL(14, pins.size());
}

// Row and column pins should not overlap
void test_row_col_pins_no_overlap(void) {
    std::set<int> row_pins = {ROW_0, ROW_1, ROW_2, ROW_3, ROW_4};
    std::set<int> col_pins = {COL_0, COL_1, COL_2, COL_3, COL_4, COL_5, COL_6,
                               COL_7, COL_8, COL_9, COL_10, COL_11, COL_12, COL_13};

    for (int row_pin : row_pins) {
        TEST_ASSERT_EQUAL(0, col_pins.count(row_pin));
    }
}

// Verify specific CC assignments haven't drifted
void test_encoder_cc_assignments(void) {
    // These are the expected CC values per the original design
    TEST_ASSERT_EQUAL(3, ENCODER_1);
    TEST_ASSERT_EQUAL(9, ENCODER_2);
    TEST_ASSERT_EQUAL(14, ENCODER_3);
    TEST_ASSERT_EQUAL(15, ENCODER_4);
}

int main(int argc, char **argv) {
    UNITY_BEGIN();

    RUN_TEST(test_cc_values_in_valid_midi_range);
    RUN_TEST(test_cc_values_non_negative);
    RUN_TEST(test_row_pins_unique);
    RUN_TEST(test_col_pins_unique);
    RUN_TEST(test_row_col_pins_no_overlap);
    RUN_TEST(test_encoder_cc_assignments);

    return UNITY_END();
}
