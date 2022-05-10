export type EthereumAddress = string; // TODO: improve

export type Chain = {
  identifier: number;
  name: string;
  rpcUrl: string; // TODO: maybe URL?
  requestManagerAddress: EthereumAddress;
  fillManagerAddress: EthereumAddress;
  explorerTransactionUrl: string; // TODO: maybe URL?
};

export type Token = {
  address: EthereumAddress;
  symbol: string;
  decimals: number;
};
