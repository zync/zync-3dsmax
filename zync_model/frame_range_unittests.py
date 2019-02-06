import unittest
from base_model import FrameRange


class TestFrameRange(unittest.TestCase):

  def test_should_create_correct_frame_range_with_dash(self):
    # given
    frange = '1-10'
    step = 2

    # when
    frame_range = FrameRange.from_string_and_step(frange, step)

    # then
    self.assertEqual(frame_range.start, 1)
    self.assertEqual(frame_range.end, 10)
    self.assertEqual(frame_range.step, 2)

  def test_should_create_correct_frame_range_without_dash(self):
    # given
    frange = '13'
    step = 10

    # when
    frame_range = FrameRange.from_string_and_step(frange, step)

    # then
    self.assertEqual(frame_range.start, 13)
    self.assertEqual(frame_range.end, 13)
    self.assertEqual(frame_range.step, 10)

  def test_should_return_correct_string_without_step(self):
    # given
    frame_range = FrameRange(10, 100, 1)

    # then
    self.assertEqual(frame_range.to_string_without_step(), '10-100')

  def test_should_return_correct_string_when_start_and_end_different(self):
    # given
    frame_range = FrameRange(1, 20, 3)

    # them
    self.assertEqual(str(frame_range), '1-20x3')

  def test_should_return_correct_string_when_start_and_end_equal(self):
    # given
    frame_range = FrameRange(20, 20, 3)

    # them
    self.assertEqual(str(frame_range), '20-20x3')


def main():
  unittest.main()


if __name__ == '__main__':
  main()
