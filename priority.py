import simpy
import random
import numpy as np
import time

VOICE_ARRIVAL_RATE = 10
VIDEO_ARRIVAL_RATE = 15
DATA_ARRIVAL_RATE = 5

VOICE_SERVICE_RATE = 60
VIDEO_SERVICE_RATE = 30
DATA_SERVICE_RATE = 20


QUEUE_CAPACITY = 30
SIM_TIME = 3600

class PriorityQueue:
    def __init__(self, env, queue_capacity):
        self.env = env
        self.server = simpy.PriorityResource(env, capacity=1)
        self.queue_capacity = queue_capacity

        self.latencies_voice, self.latencies_video, self.latencies_data = [], [], []
        self.packet_losses_voice, self.packet_losses_video, self.packet_losses_data = 0, 0, 0
        self.total_packets_voice, self.total_packets_video, self.total_packets_data = 0, 0, 0

        self.env.process(self.packet_arrival("Voice", VOICE_ARRIVAL_RATE, VOICE_SERVICE_RATE, priority=1))
        self.env.process(self.packet_arrival("Video", VIDEO_ARRIVAL_RATE, VIDEO_SERVICE_RATE, priority=2))
        self.env.process(self.packet_arrival("Data", DATA_ARRIVAL_RATE, DATA_SERVICE_RATE, priority=3))

    def packet_arrival(self, packet_type, arrival_rate, service_rate, priority):
        while True:
            inter_arrival_time = random.expovariate(arrival_rate)
            yield self.env.timeout(inter_arrival_time)

            if packet_type == "Voice":
                self.total_packets_voice += 1
            elif packet_type == "Video":
                self.total_packets_video += 1
            else:
                self.total_packets_data += 1

            current_queue_length = self.server.count + len(self.server.queue)
            print(f"[{self.env.now:.2f} s] {packet_type} Packet arrived. Queue length: {current_queue_length}")

            if current_queue_length >= self.queue_capacity:
                if packet_type == "Voice":
                    self.packet_losses_voice += 1
                elif packet_type == "Video":
                    self.packet_losses_video += 1
                else:
                    self.packet_losses_data += 1

                print(f"[{self.env.now:.2f} s] {packet_type} Packet dropped! Queue full (Length: {current_queue_length}).")
            else:
                print(f"[{self.env.now:.2f} s] {packet_type} Packet enqueued for service.")
                self.env.process(self.packet_service(packet_type, service_rate, priority))

    def packet_service(self, packet_type, service_rate, priority):
        arrival_time = self.env.now
        with self.server.request(priority=priority, preempt=True) as request:
            yield request
            print(f"[{self.env.now:.2f} s] {packet_type} Packet started service.")

            service_time = random.expovariate(service_rate)
            yield self.env.timeout(service_time)
            latency = self.env.now - arrival_time

            if packet_type == "Voice":
                self.latencies_voice.append(latency)
            elif packet_type == "Video":
                self.latencies_video.append(latency)
            else:
                self.latencies_data.append(latency)

            print(f"[{self.env.now:.2f} s] {packet_type} Packet completed service. Latency: {latency:.2f} s")

def results(queue):
    traffic_types = {
        "Voice": (queue.latencies_voice, queue.packet_losses_voice, queue.total_packets_voice),
        "Video": (queue.latencies_video, queue.packet_losses_video, queue.total_packets_video),
        "Data": (queue.latencies_data, queue.packet_losses_data, queue.total_packets_data),
    }

    for traffic, (latencies, packet_losses, total_packets) in traffic_types.items():
        avg_latency = np.mean(latencies)

        deviations = [abs(latency - avg_latency) for latency in latencies]
        jitter = np.mean(deviations)
        loss_rate = (packet_losses / total_packets) * 100

        print(f"{traffic} Traffic:")
        print(f"  Total packets: {total_packets}")
        print(f"  Packets lost: {packet_losses}")
        print(f"  Average Latency: {avg_latency * 1000:.2f} ms")
        print(f"  Jitter: {jitter * 1000:.2f} ms")
        print(f"  Packet Loss Rate: {loss_rate:.2f}%")
        print("-" * 40)

def run_simulation():
    env = simpy.Environment()
    queue = PriorityQueue(env, QUEUE_CAPACITY)

    time.sleep(1),print("--- Simulation Start ---")
    time.sleep(1),print(f"Queue Capacity: {QUEUE_CAPACITY} packets")
    time.sleep(1),print(f"Simulation Time: {SIM_TIME} seconds\n")
    time.sleep(2)

    env.run(until=SIM_TIME)
    print(), print("--- Simulation Results (priority) ---")
    results(queue)

run_simulation()
