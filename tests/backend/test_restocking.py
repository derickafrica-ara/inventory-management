"""
Tests for restocking API endpoints (demand forecast pricing, restock orders).
"""
import pytest

from mock_data import restock_orders


@pytest.fixture(autouse=True)
def clear_restock_orders():
    """Restock orders live in a module-level list, so reset it around each test."""
    restock_orders.clear()
    yield
    restock_orders.clear()


class TestRestockingDemandData:
    """Test suite for the pricing fields restocking adds to demand forecasts."""

    def test_demand_forecasts_include_restock_fields(self, client):
        """Test that every forecast carries cost, supplier and lead time."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        for forecast in data:
            assert isinstance(forecast["unit_cost"], (int, float))
            assert forecast["unit_cost"] > 0
            assert isinstance(forecast["supplier"], str)
            assert isinstance(forecast["lead_time_days"], int)
            assert forecast["lead_time_days"] > 0


class TestRestockOrderEndpoints:
    """Test suite for restock order submission and listing."""

    def _forecasts(self, client):
        return {f["item_sku"]: f for f in client.get("/api/demand").json()}

    def test_get_restock_orders_empty(self, client):
        """Test that no orders are listed before any are submitted."""
        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_restock_order(self, client):
        """Test submitting a valid order computes totals and lead time."""
        forecasts = self._forecasts(client)
        skus = list(forecasts)[:2]
        quantities = {skus[0]: 10, skus[1]: 5}
        expected_total = sum(forecasts[s]["unit_cost"] * q for s, q in quantities.items())
        expected_lead = max(forecasts[s]["lead_time_days"] for s in skus)

        response = client.post("/api/restock-orders", json={
            "items": [{"sku": s, "quantity": q} for s, q in quantities.items()],
            "budget": expected_total + 100,
        })
        assert response.status_code == 200

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")
        assert abs(order["total_cost"] - expected_total) < 0.01
        assert order["lead_time_days"] == expected_lead
        assert len(order["items"]) == 2
        assert "T" in order["expected_delivery"]

    def test_created_order_is_listed_newest_first(self, client):
        """Test that submitted orders appear in the list, newest first."""
        forecasts = self._forecasts(client)
        sku = next(iter(forecasts))
        budget = forecasts[sku]["unit_cost"] * 10

        first = client.post("/api/restock-orders", json={
            "items": [{"sku": sku, "quantity": 1}], "budget": budget}).json()
        second = client.post("/api/restock-orders", json={
            "items": [{"sku": sku, "quantity": 2}], "budget": budget}).json()

        listed = client.get("/api/restock-orders").json()
        assert [o["id"] for o in listed] == [second["id"], first["id"]]

    def test_server_uses_forecast_costs_not_client_values(self, client):
        """Test that extra client-supplied price fields are ignored."""
        forecasts = self._forecasts(client)
        sku = next(iter(forecasts))
        unit_cost = forecasts[sku]["unit_cost"]

        response = client.post("/api/restock-orders", json={
            "items": [{"sku": sku, "quantity": 3, "unit_cost": 0.01}],
            "budget": unit_cost * 3,
        })
        assert response.status_code == 200
        assert abs(response.json()["total_cost"] - unit_cost * 3) < 0.01

    def test_create_order_does_not_change_regular_orders(self, client):
        """Test that restock orders stay out of /api/orders and dashboard totals."""
        orders_before = len(client.get("/api/orders").json())
        summary_before = client.get("/api/dashboard/summary").json()

        forecasts = self._forecasts(client)
        sku = next(iter(forecasts))
        client.post("/api/restock-orders", json={
            "items": [{"sku": sku, "quantity": 1}], "budget": forecasts[sku]["unit_cost"]})

        assert len(client.get("/api/orders").json()) == orders_before
        assert client.get("/api/dashboard/summary").json() == summary_before

    def test_create_order_empty_items(self, client):
        """Test that an order with no items is rejected."""
        response = client.post("/api/restock-orders", json={"items": [], "budget": 1000})
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_create_order_zero_quantity(self, client):
        """Test that a zero quantity is rejected."""
        sku = next(iter(self._forecasts(client)))
        response = client.post("/api/restock-orders", json={
            "items": [{"sku": sku, "quantity": 0}], "budget": 1000})
        assert response.status_code == 400

    def test_create_order_over_budget(self, client):
        """Test that an order exceeding the budget is rejected and not stored."""
        forecasts = self._forecasts(client)
        sku = next(iter(forecasts))
        response = client.post("/api/restock-orders", json={
            "items": [{"sku": sku, "quantity": 10}],
            "budget": forecasts[sku]["unit_cost"] * 10 - 1,
        })
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()
        assert client.get("/api/restock-orders").json() == []

    def test_create_order_unknown_sku(self, client):
        """Test that an unknown SKU returns 404."""
        response = client.post("/api/restock-orders", json={
            "items": [{"sku": "NOPE-999", "quantity": 1}], "budget": 1000})
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_order_duplicate_sku(self, client):
        """Test that duplicate SKUs in one order are rejected."""
        sku = next(iter(self._forecasts(client)))
        response = client.post("/api/restock-orders", json={
            "items": [{"sku": sku, "quantity": 1}, {"sku": sku, "quantity": 1}],
            "budget": 100000})
        assert response.status_code == 400

    def test_create_order_invalid_body(self, client):
        """Test that a malformed body returns a validation error."""
        response = client.post("/api/restock-orders", json={"budget": 100})
        assert response.status_code == 422
