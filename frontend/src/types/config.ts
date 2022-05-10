import type { Chain, Token } from './data';

export interface ChainWithTokens extends Chain {
  tokens: Token[];
}

export type BeamerConfig = {
  chains: {
    [chainId: string]: ChainWithTokens;
  };
};
