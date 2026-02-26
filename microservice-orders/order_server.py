import os
from concurrent import futures

import grpc

import orders_pb2
import orders_pb2_grpc

import usercarts_pb2
import usercarts_pb2_grpc

CARTS_GRPC_TARGET = os.environ.get("CARTS_GRPC_TARGET", "microservice-usercarts:50053")


class OrdersService(orders_pb2_grpc.OrdersServiceServicer):
    def __init__(self):
        self._channel = grpc.insecure_channel(CARTS_GRPC_TARGET)
        self._carts = usercarts_pb2_grpc.UserCartsServiceStub(self._channel)

    def PlaceOrder(self, request, context):
        user_id = (request.user_id or "").strip()
        if not user_id:
            return orders_pb2.PlaceOrderResponse(ok=False, message="Missing user_id")

        # Later you’d validate totals, charge payment, save an order record, etc.
        cleared = self._carts.ClearCart(usercarts_pb2.ClearCartRequest(user_id=user_id))
        if not cleared.ok:
            return orders_pb2.PlaceOrderResponse(ok=False, message=cleared.message or "Failed to clear cart")

        return orders_pb2.PlaceOrderResponse(ok=True, message="Order placed (cart cleared)")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    orders_pb2_grpc.add_OrdersServiceServicer_to_server(OrdersService(), server)
    server.add_insecure_port("0.0.0.0:50054")
    server.start()
    print("Orders gRPC server listening on 0.0.0.0:50054")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()