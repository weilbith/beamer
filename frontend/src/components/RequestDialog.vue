<template>
  <div class="request-dialog">
    <div class="h-14">
      <div v-if="ethereumProvider.signer" class="flex flex-row gap-4 justify-center items-center">
        <div class="h-7 w-7 rounded-50 border-4 border-solid border-teal-light bg-green"></div>
        <span class="text-lg">You are currently connected via Metamask</span>
      </div>
    </div>
    <FormKit
      ref="requestForm"
      v-slot="{ state: { valid } }"
      form-class="flex flex-col items-center"
      type="form"
      :actions="false"
      @submit="submitRequestTransaction"
    >
      <Card class="bg-teal px-20 pt-18 pb-16 self-stretch mb-11">
        <RequestFormInputs v-if="!isTransferInProgress" />
        <TransferStatus v-else :transfer="transfer" />
        <Transition name="expand">
          <div v-if="shownError" class="mt-7 text-right text-lg text-orange-dark">
            {{ shownError }}
          </div>
        </Transition>
      </Card>

      <div v-if="!ethereumProvider.signer">
        <FormKit
          input-class="w-112 bg-orange flex flex-row justify-center"
          type="button"
          @click="runRequestSigner"
        >
          <div v-if="requestSignerActive" class="h-8 w-8">
            <spinner></spinner>
          </div>
          <template v-else>Connect MetaMask Wallet</template>
        </FormKit>
      </div>
      <div v-else>
        <FormKit
          v-if="!isTransferInProgress"
          class="w-72 flex flex-row justify-center bg-green"
          type="submit"
          :disabled="!valid"
        >
          Transfer funds
        </FormKit>

        <FormKit
          v-if="transfer"
          input-class="w-72 flex flex-row justify-center bg-green"
          type="button"
          :disabled="isNewTransferDisabled"
          @click="newTransfer"
          >New Transfer</FormKit
        >
      </div>
    </FormKit>
  </div>
</template>

<script setup lang="ts">
import { FormKitFrameworkContext } from '@formkit/core';
import { FormKit } from '@formkit/vue';
import { storeToRefs } from 'pinia';
import { computed, ref, watch } from 'vue';

import { Transfer } from '@/actions/transfer';
import Card from '@/components/layout/Card.vue';
import RequestFormInputs from '@/components/RequestFormInputs.vue';
import Spinner from '@/components/Spinner.vue';
import TransferStatus from '@/components/TransferStatus.vue';
import { useRequestFee } from '@/composables/useRequestFee';
import { useRequestSigner } from '@/composables/useRequestSigner';
import { useConfiguration } from '@/stores/configuration';
import { useEthereumProvider } from '@/stores/ethereum-provider';
import type { Chain } from '@/types/data';
import type { SelectorOption } from '@/types/form';

interface Emits {
  (e: 'reload'): void;
}

const emit = defineEmits<Emits>();

const configuration = useConfiguration();
const ethereumProvider = useEthereumProvider();
const { provider, signer, signerAddress, chainId } = storeToRefs(ethereumProvider);

const transfer = ref<Transfer | undefined>(undefined);
const requestForm = ref<FormKitFrameworkContext>();

const requestManagerAddress = computed(
  () => configuration.chains[chainId.value]?.requestManagerAddress,
);

const { amount: requestFeeAmount } = useRequestFee(provider, requestManagerAddress);

const {
  run: requestSigner,
  active: requestSignerActive,
  error: requestSignerError,
} = useRequestSigner();

const runRequestSigner = () => {
  // TOOD: In future we will not separate getting provider and signer which
  // resolve the undefined provider case.
  if (provider.value) {
    requestSigner(provider.value);
  }
};

const newTransfer = async () => {
  emit('reload');
};

const submitRequestTransaction = async (formResult: {
  amount: string;
  fromChainId: SelectorOption;
  toChainId: SelectorOption;
  toAddress: string;
  tokenAddress: SelectorOption;
}) => {
  if (!provider.value || !signer.value) {
    throw new Error('No signer available!');
  }

  const sourceChainConfiguration = configuration.chains[formResult.fromChainId.value];
  const sourceChain: Chain = {
    identifier: sourceChainConfiguration.identifier,
    name: sourceChainConfiguration.name,
    rpcUrl: sourceChainConfiguration.rpcUrl,
    requestManagerAddress: sourceChainConfiguration.requestManagerAddress,
    fillManagerAddress: sourceChainConfiguration.fillManagerAddress,
    explorerTransactionUrl: sourceChainConfiguration.explorerTransactionUrl,
  };
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const sourceToken = sourceChainConfiguration.tokens.find(
    (token) => token.symbol === formResult.tokenAddress.label,
  )!;

  const targetChainConfiguration = configuration.chains[formResult.toChainId.value];
  const targetChain: Chain = {
    identifier: targetChainConfiguration.identifier,
    name: targetChainConfiguration.name,
    rpcUrl: targetChainConfiguration.rpcUrl,
    requestManagerAddress: targetChainConfiguration.requestManagerAddress,
    fillManagerAddress: targetChainConfiguration.fillManagerAddress,
    explorerTransactionUrl: targetChainConfiguration.explorerTransactionUrl,
  };
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const targetToken = targetChainConfiguration.tokens.find(
    (token) => token.symbol === formResult.tokenAddress.label,
  )!;

  transfer.value = new Transfer({
    amount: Number(formResult.amount),
    sourceChain,
    sourceToken,
    targetChain,
    targetToken,
    targetAccount: formResult.toAddress,
    validityPeriod: 600,
    fees: requestFeeAmount.value,
  });

  try {
    await transfer.value.execute(signer.value, signerAddress.value);
  } catch (error) {
    console.error(error);
    console.log(transfer.value);
  }
};

watch(chainId, () => location.reload());

const isTransferInProgress = computed(() => {
  return transfer.value && (transfer.value.active || transfer.value.done);
});

const isNewTransferDisabled = computed(() => {
  return transfer.value !== undefined && !transfer.value.done;
});

const shownError = computed(() => {
  return requestSignerError.value || transfer.value?.errorMessage;
});
</script>
