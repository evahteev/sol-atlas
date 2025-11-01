import { ChainModel } from '@/models/chain'
import { TransactionModel } from '@/models/history'

export type RowVarsProps = {
  chain?: ChainModel
}

export const getRowVars =
  (chains: ChainModel[]) =>
  (data?: Partial<TransactionModel>): RowVarsProps => {
    const result: RowVarsProps = {}

    if (!data) {
      return result
    }

    return {
      chain: chains?.find((chain) => chain.name === data.network),
    }
  }
