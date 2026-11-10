from budget_app.common.errors import ConflictError, NotFoundError, ValidationError
from budget_app.services.categories import CategoryService
from tests.support import StoreCase


class CategoryTests(StoreCase):
    def setUp(self):
        super().setUp()
        self.service = CategoryService(self.categories, self.transactions)

    def test_add_list_remove(self):
        self.assertEqual(self.service.add(' 취미 '), '취미')
        self.assertIn('취미', self.service.list_all())
        self.service.remove('취미')
        self.assertNotIn('취미', self.categories.list_all())

    def test_duplicate_missing_and_empty(self):
        with self.assertRaises(ConflictError):
            self.service.add('food')
        with self.assertRaises(NotFoundError):
            self.service.remove('missing')
        with self.assertRaises(ValidationError):
            self.service.add('  ')

    def test_used_category_cannot_be_removed(self):
        self.seed(self.transaction())
        before = self.categories.path.read_bytes()
        with self.assertRaises(ConflictError):
            self.service.remove('food')
        self.assertEqual(self.categories.path.read_bytes(), before)
        self.assertFalse((self.store.root / '.write.lock').exists())

    def test_empty_category_list_can_be_repopulated(self):
        self.categories.save_all([])
        self.assertEqual(self.service.list_all(), [])
        self.service.add('새분류')
        self.assertEqual(self.service.list_all(), ['새분류'])
