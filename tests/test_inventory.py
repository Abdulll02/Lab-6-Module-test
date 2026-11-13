"""Тесты для модуля складского учёта src/inventory.py."""

import pytest

from src.inventory import (
    Inventory,
    Item,
    OutOfStockError,
    UnknownItemError,
)


@pytest.fixture
def inventory():
    """Склад с одной позицией: 10 яблок по 10.0 (стоимость 100.0)."""
    inv = Inventory()
    inv.add(Item("apple", 10.0), quantity=10)
    return inv


@pytest.fixture
def mixed_inventory():
    """Склад с несколькими позициями разной стоимости и количества."""
    inv = Inventory()
    inv.add(Item("apple", 10.0), quantity=10)
    inv.add(Item("banana", 30.0), quantity=2)
    inv.add(Item("cherry", 0.5), quantity=3)
    return inv


# --- Item -----------------------------------------------------------------


def test_item_create_valid_sets_fields():
    item = Item("milk", 2.5, quantity=7)

    assert item.name == "milk"
    assert item.price == pytest.approx(2.5)
    assert item.quantity == 7


def test_item_create_without_quantity_defaults_to_zero():
    item = Item("bread", 1.0)

    assert item.quantity == 0


@pytest.mark.parametrize("name", ["", None])
def test_item_create_empty_name_raises_value_error(name):
    with pytest.raises(ValueError):
        Item(name, 1.0)


def test_item_create_negative_price_raises_value_error():
    with pytest.raises(ValueError):
        Item("milk", -0.01)


def test_item_create_negative_quantity_raises_value_error():
    with pytest.raises(ValueError):
        Item("milk", 1.0, quantity=-1)


# --- Inventory.add --------------------------------------------------------


def test_add_new_item_stores_item_with_given_quantity():
    inv = Inventory()
    item = Item("milk", 2.5, quantity=7)

    inv.add(item, quantity=3)

    assert inv.find("milk") is item
    assert inv.find("milk").quantity == 3


def test_add_existing_item_increases_quantity(inventory):
    inv = inventory
    another_apple = Item("apple", 10.0, quantity=999)

    inv.add(another_apple, quantity=5)

    assert inv.find("apple").quantity == 15
    assert inv.find("apple") is not another_apple


@pytest.mark.parametrize("quantity", [0, -1, -100])
def test_add_non_positive_quantity_raises_value_error(inventory, quantity):
    with pytest.raises(ValueError):
        inventory.add(Item("pear", 5.0), quantity=quantity)


# --- Inventory.remove -----------------------------------------------------


def test_remove_decreases_quantity(inventory):
    inventory.remove("apple", quantity=4)

    assert inventory.find("apple").quantity == 6


def test_remove_exact_quantity_deletes_item(inventory):
    inventory.remove("apple", quantity=10)

    with pytest.raises(UnknownItemError):
        inventory.find("apple")


def test_remove_unknown_item_raises_unknown_item_error(inventory):
    with pytest.raises(UnknownItemError):
        inventory.remove("banana")


def test_remove_more_than_available_raises_out_of_stock_error(inventory):
    with pytest.raises(OutOfStockError):
        inventory.remove("apple", quantity=11)


@pytest.mark.parametrize("quantity", [0, -1])
def test_remove_non_positive_quantity_raises_value_error(inventory, quantity):
    with pytest.raises(ValueError):
        inventory.remove("apple", quantity=quantity)


def test_remove_default_quantity_one_decreases_by_one(inventory):
    inventory.remove("apple")

    assert inventory.find("apple").quantity == 9


# --- Inventory.find -------------------------------------------------------


def test_find_existing_item_returns_same_item(inventory):
    assert inventory.find("apple").price == pytest.approx(10.0)
    assert inventory.find("apple").quantity == 10


def test_find_unknown_item_raises_unknown_item_error(inventory):
    with pytest.raises(UnknownItemError):
        inventory.find("banana")


# --- Inventory.total_value ------------------------------------------------


def test_total_value_empty_inventory_is_zero():
    assert Inventory().total_value() == pytest.approx(0.0)


def test_total_value_single_item_is_price_times_quantity(inventory):
    assert inventory.total_value() == pytest.approx(100.0)


def test_total_value_multiple_items_sums_all_positions(mixed_inventory):
    assert mixed_inventory.total_value() == pytest.approx(161.5)


# --- Inventory.low_stock --------------------------------------------------


def test_low_stock_default_threshold_returns_items_up_to_five():
    inv = Inventory()
    inv.add(Item("a", 1.0), quantity=1)
    inv.add(Item("b", 1.0), quantity=5)
    inv.add(Item("c", 1.0), quantity=6)

    assert inv.low_stock() == ["a", "b"]


def test_low_stock_explicit_threshold_returns_items_up_to_threshold():
    inv = Inventory()
    inv.add(Item("a", 1.0), quantity=2)
    inv.add(Item("b", 1.0), quantity=3)
    inv.add(Item("c", 1.0), quantity=4)

    assert inv.low_stock(threshold=3) == ["a", "b"]


def test_low_stock_returns_names_sorted_alphabetically():
    inv = Inventory()
    inv.add(Item("cherry", 1.0), quantity=1)
    inv.add(Item("apple", 1.0), quantity=1)
    inv.add(Item("banana", 1.0), quantity=1)

    assert inv.low_stock(threshold=1) == ["apple", "banana", "cherry"]


def test_low_stock_zero_threshold_returns_only_empty_items():
    inv = Inventory()
    inv.add(Item("a", 1.0), quantity=1)

    assert inv.low_stock(threshold=0) == []


def test_low_stock_empty_inventory_returns_empty_list():
    assert Inventory().low_stock() == []


def test_low_stock_negative_threshold_raises_value_error(inventory):
    with pytest.raises(ValueError):
        inventory.low_stock(threshold=-1)


# --- Inventory.apply_discount ---------------------------------------------


@pytest.mark.parametrize(
    "percent, expected",
    [
        (0, 100.0),
        (10, 90.0),
        (50, 50.0),
        (100, 0.0),
    ],
)
def test_apply_discount_valid_percent_returns_discounted_value(
    inventory, percent, expected
):
    assert inventory.apply_discount(percent) == pytest.approx(expected)


@pytest.mark.parametrize("percent", [-1, 100.01, 101])
def test_apply_discount_out_of_range_percent_raises_value_error(
    inventory, percent
):
    with pytest.raises(ValueError):
        inventory.apply_discount(percent)


def test_apply_discount_empty_inventory_is_zero():
    assert Inventory().apply_discount(10) == pytest.approx(0.0)
