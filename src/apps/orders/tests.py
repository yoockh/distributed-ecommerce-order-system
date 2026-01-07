from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from apps.catalog.models import Product
from apps.orders.models import Order
from apps.orders.services import OutOfStock, ProductNotFound, purchase_product


class PurchaseProductServiceTests(TestCase):
	def setUp(self) -> None:
		self.product = Product.objects.create(
			name="Test Product",
			price=Decimal("199.99"),
			stock=5,
		)

	@patch("apps.orders.services.process_order.delay")
	def test_purchase_successfully_decrements_stock_and_enqueues_worker(self, mock_delay):
		order = purchase_product(product_id=self.product.id, quantity=2)

		self.product.refresh_from_db()

		self.assertIsInstance(order, Order)
		self.assertEqual(order.product_id, self.product.id)
		self.assertEqual(order.quantity, 2)
		self.assertEqual(self.product.stock, 3)
		mock_delay.assert_called_once_with(order.id)

	def test_purchase_product_not_found_raises(self):
		with self.assertRaises(ProductNotFound):
			purchase_product(product_id=9999, quantity=1)

	def test_purchase_out_of_stock_raises(self):
		with self.assertRaises(OutOfStock):
			purchase_product(product_id=self.product.id, quantity=10)
