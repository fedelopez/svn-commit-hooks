library dart_test;

import 'package:unittest/unittest.dart';

main() {
  solo_group('dart test', () {
    test('dart sample test', () {
      List<String> list = ["a", "b", "c"];
      expect(list.length, 3);
    });
  });
}
