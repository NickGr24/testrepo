import unittest
# from main import calc

# class TestCalcFunction(unittest.TestCase):
#     def test_calc(self):
#         self.assertEqual(calc(2, 3), 5)
#         self.assertEqual(calc(-1, 1), 0) # assertEqual = проверяет равенство между двумя значениями

# 
#     def test_if_true(self):
#         is_student = False

#         self.assertTrue(is_student)  # assertTrue = проверяет, что значение истинно
class TestSomething(unittest.TestCase):
    def test_if_is_in(self):
        fruits = ['apple', 'banana', 'cherry']

        name = 'Nikita'
        self.assertIn('ta', name)  # assertIn = проверяет, что подстрока присутствует в строке
        self.assertIn('banana', fruits)  # assertIn = проверяет, что элемент присутствует в контейнере
    
    def test_if_is_the_same_object(self):
        a = 3
        b = a
        self.assertIs(a, b)  # assertIs = проверяет, что два объекта являются одним и тем же объектом в памяти    


if __name__ == '__main__':
    unittest.main()
    
