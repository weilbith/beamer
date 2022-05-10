export class JsonRpcProvider {
  readonly connection: { url: string };

  constructor(url?: string) {
    this.connection = { url: url ?? 'https://test.rpc' };
  }

  public getBlockNumber = vi.fn().mockResolvedValue(1);
}

export class JsonRpcSigner {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  readonly connectionGuard: any;
  readonly provider: JsonRpcProvider;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  constructor(connectionGuard: any, provider: JsonRpcProvider) {
    this.connectionGuard = connectionGuard;
    this.provider = provider;
  }
}
