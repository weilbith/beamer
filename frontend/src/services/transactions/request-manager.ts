import { JsonRpcProvider, JsonRpcSigner, TransactionResponse } from '@ethersproject/providers';
import { Contract } from 'ethers';

import RequestManager from '@/assets/RequestManager.json';
import type { EthereumProvider } from '@/services/web3-provider';
import type { EthereumAddress } from '@/types/data';

export async function getRequestFee(
  provider: EthereumProvider,
  requestManagerAddress: string,
): Promise<number> {
  const requestManagerContract = new Contract(requestManagerAddress, RequestManager.abi);
  const connectedContract = provider.connectContract(requestManagerContract);
  return await connectedContract.totalFee();
}

export async function sendRequestTransaction(
  signer: JsonRpcSigner,
  amount: number,
  targetChainIdentifier: number,
  requestManagerAddress: EthereumAddress,
  sourceTokenAddress: EthereumAddress,
  targetTokenAddress: EthereumAddress,
  targetAccount: EthereumAddress,
  validityPeriod: number,
  fees: number, // TODO: BigNumber ?
): Promise<string> {
  const requestManagerContract = new Contract(requestManagerAddress, RequestManager.abi, signer);

  const requestParameter = [
    targetChainIdentifier,
    sourceTokenAddress,
    targetTokenAddress,
    targetAccount,
    amount, // TODO: BigNumber ?
    validityPeriod, // TODO: BigNumber ?
  ];

  const estimatedGasLimit = await requestManagerContract.estimateGas.createRequest(
    ...requestParameter,
    { value: fees },
  );

  const transaction: TransactionResponse = await requestManagerContract.createRequest(
    ...requestParameter,
    { value: fees, gasLimit: estimatedGasLimit },
  );

  return transaction.hash;
}

export async function getRequestIdentifier(
  provider: JsonRpcProvider,
  requestManagerAddress: EthereumAddress,
  transactionHash: string,
): Promise<number> {
  const requestManagerContract = new Contract(requestManagerAddress, RequestManager.abi, provider);
  const receipt = await provider.getTransactionReceipt(transactionHash);
  const event = requestManagerContract.interface.parseLog(receipt.logs[0]);

  if (event) {
    return event.args.requestId.toNumber(); // TODO: check this typing
  } else {
    throw new Error("Request Failed. Couldn't retrieve Request ID");
  }
}
