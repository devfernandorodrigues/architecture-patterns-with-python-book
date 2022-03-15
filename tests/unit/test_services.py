from datetime import datetime, timedelta
import pytest
import domain.model as model
import service_layer.services as services
from adapters.repository import FakeRepository
from service_layer import unit_of_work


tomorrow = datetime.now() + timedelta(days=1)


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.batches = FakeRepository([])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_returns_allocation():
    uow = FakeUnitOfWork()
    services.add_batch("batch1", "COMPLICATED-LAMP", 100, None, uow)

    result = services.allocate("o1", "COMPLICATED-LAMP", 10, uow)

    assert result == "batch1"


def test_error_for_invalid_sku():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "AREALSKU", 100, None, uow)

    with pytest.raises(
        services.InvalidSku, match="Invalid sku NONEXISTENTSKU"
    ):
        services.allocate("o1", "NONEXISTENTSKU", 10, uow)


def test_commits():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "OMINOUS-MIRROR", 100, None, uow)

    services.allocate("o1", "OMINOUS-MIRROR", 10, uow)

    assert uow.committed is True


def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = model.Batch(
        "in-stock-batch", "RETRO-CLOCK", 100, eta=None
    )
    shipment_batch = model.Batch(
        "shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow
    )
    line = model.OrderLine("oref", "RETRO-CLOCK", 10)

    model.allocate(line, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_warehouse_batches_to_shipments():
    uow = FakeUnitOfWork()
    services.add_batch("in-stock-batch", "RETRO-CLOCK", 100, None, uow)
    services.add_batch("shipment-batch", "RETRO-CLOCK", 100, tomorrow, uow)

    batchref = services.allocate("oref", "RETRO-CLOCK", 10, uow)

    assert batchref == "in-stock-batch"


def test_add_batch():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)
    assert uow.batches.get("b1") is not None
    assert uow.committed


def test_allocate_returns_allocation():
    uow = FakeUnitOfWork()
    services.add_batch("batch1", "COMPLICATED-LAMP", 100, None, uow)
    result = services.allocate("o1", "COMPLICATED-LAMP", 10, uow)
    assert result == "batch1"


def test_allocate_errors_for_invalid_sku():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "AREALSKU", 100, None, uow)

    with pytest.raises(
        services.InvalidSku, match="Invalid sku NONEXISTENTSKU"
    ):
        services.allocate("o1", "NONEXISTENTSKU", 10, uow)
