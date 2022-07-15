<template>
  <div class="flex flex-col justify-center items-center h-full" :class="backgroundClasses">
    <div class="text-[30rem] font-mono">{{ formattedTime }}s</div>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';

import { getCurrentBlockNumber, waitForFulfillment } from '@/services/transactions/fill-manager';
import { waitForNextRequest } from '@/services/transactions/request-manager';
import { useConfiguration } from '@/stores/configuration';
import { UInt256 } from '@/types/uint-256';

const time = ref(0); // milliseconds
const formattedTime = computed(() => formatTime(time.value));
const timerInterval = ref<ReturnType<typeof setInterval> | undefined>(undefined);

const configuration = useConfiguration();
const sourceChain = computed(() => configuration.chains[28]);
const targetChain = computed(() => configuration.chains[588]);

const backgroundClasses = ref({});

function formatTime(milliseconds: number): string {
  const beforeDot = Math.floor(milliseconds / 1000);
  const afterDot = Math.floor((milliseconds % 1000) / 100);

  return `${beforeDot}.${afterDot}`;
}

function startTimer(): void {
  time.value = 0;
  const intervalDuration = 100;
  const incrementTime = () => (time.value += intervalDuration);

  timerInterval.value = setInterval(incrementTime, intervalDuration);
}

function stopTimer(): void {
  if (timerInterval.value) {
    clearInterval(timerInterval.value);
  }
}

function sleep(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function flashBackground(colorClass: string, times = 2) {
  for (let i = 0; i < times; i++) {
    backgroundClasses.value = { [colorClass]: true };
    await sleep(200);
    backgroundClasses.value = { [colorClass]: false };
    await sleep(200);
  }
}

async function main(): Promise<void> {
  let lastRequestIdentifier = new UInt256('0');

  /* eslint-disable no-constant-condition */
  while (true) {
    const blockNumber = await getCurrentBlockNumber(targetChain.value.rpcUrl);
    const requestIdentifier = await waitForNextRequest(
      sourceChain.value.rpcUrl,
      sourceChain.value.requestManagerAddress,
    );

    // Sometimes we see the event twice, I don't know why, I don't care for this
    // stupid feature...
    if (requestIdentifier.asString == lastRequestIdentifier.asString) {
      continue;
    }

    lastRequestIdentifier = requestIdentifier;

    startTimer();
    flashBackground('bg-teal-light', 1);

    const { promise: fulfillmentPromise } = waitForFulfillment(
      targetChain.value.rpcUrl,
      targetChain.value.fillManagerAddress,
      requestIdentifier,
      blockNumber,
    );

    await fulfillmentPromise;

    stopTimer();
    flashBackground('bg-green', 2);
    await sleep(5000); // To guarantee the result is shown at least for a moment.
  }
}

onMounted(main);
</script>
