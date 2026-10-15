"""Synthetic policy specification, NOT a wallet, signer or on-chain restriction.

Only synthetic intents can be processed. This memory-only model is not a secure
boundary against a compromised host and must not be attached to live execution.
Notional limits bound authorized turnover, not investment capital or market loss.
"""
from dataclasses import dataclass
from threading import RLock

MAX_ATOMIC = 2**256 - 1


def integer(value: object, name: str, minimum: int = 0) -> int:
    if type(value) is not int or not minimum <= value <= MAX_ATOMIC:
        raise ValueError(f'{name}: bounded integer >= {minimum} required')
    return value


@dataclass(frozen=True)
class Policy:
    initial_micro_usd: int = 100_000_000
    reserve_micro_usd: int = 10_000_000
    max_order_micro_usd: int = 25_000_000
    max_notional_24h_micro_usd: int = 60_000_000
    lifetime_notional_micro_usd: int = 100_000_000
    max_fee_per_attempt_micro_usd: int = 100_000
    total_fee_budget_micro_usd: int = 1_000_000
    max_attempts_24h: int = 10
    max_slippage_bps: int = 100
    max_quote_age_s: int = 30
    valid_from: int = 0
    valid_until: int = 172800
    chain_id: int = 8453
    route: str = 'SIM_ROUTER'
    recipient: str = 'SIM_TRADING'
    selector: str = 'exactInputSingle'
    token_in: str = 'SIM_USDC'
    token_out: str = 'SIM_WETH'


@dataclass(frozen=True)
class Intent:
    evidence_class: str = 'SYNTHETIC'
    action: str = 'swap'
    chain_id: int = 8453
    route: str = 'SIM_ROUTER'
    recipient: str = 'SIM_TRADING'
    selector: str = 'exactInputSingle'
    token_in: str = 'SIM_USDC'
    token_out: str = 'SIM_WETH'
    amount_in_atomic: int = 20_000_000
    quoted_out_atomic: int = 1_000_000
    minimum_out_atomic: int = 990_000
    notional_micro_usd: int = 20_000_000
    fee_upper_micro_usd: int = 10000
    observed_at: int = 1000
    deadline: int = 1060
    nonce: int = 0


class MockGate:
    """Atomic in-process intent checks; no keys, ABI, signing or network code.

    All input values (including USD valuation and fee bound) are synthetic and
    trusted only within the test model. No price-oracle truth is established.
    A fresh object is a fresh mock session, NOT a safe production restart.
    """
    def __init__(self, policy: Policy):
        if type(policy) is not Policy:
            raise ValueError('Policy required')
        for name, value in vars(policy).items():
            if name in {'route','recipient','selector','token_in','token_out'}:
                if type(value) is not str or not value or len(value) > 128:
                    raise ValueError(f'invalid {name}')
            else:
                integer(value, name)
        if not 0 < policy.initial_micro_usd <= 100_000_000:
            raise ValueError('external funding ceiling is $100')
        if not (0 < policy.max_order_micro_usd <= policy.initial_micro_usd-policy.reserve_micro_usd):
            raise ValueError('order/reserve relation')
        if not (policy.max_notional_24h_micro_usd > 0 and policy.lifetime_notional_micro_usd > 0):
            raise ValueError('turnover relation')
        if not (0 < policy.max_attempts_24h and 0 <= policy.max_slippage_bps < 10000):
            raise ValueError('attempt/slippage relation')
        if not (policy.valid_from < policy.valid_until and policy.max_quote_age_s > 0):
            raise ValueError('session/quote time relation')
        if policy.token_in == policy.token_out:
            raise ValueError('different tokens required')
        self.policy=policy
        self.next_nonce=0
        self.lifetime_notional_micro_usd=0
        self.fees_reserved_micro_usd=0
        self.last_time=policy.valid_from
        self.revoked=False
        self._attempts=[]
        self._lock=RLock()

    def revoke(self) -> None:
        """Local mock stop, not an on-chain revocation transaction."""
        with self._lock:
            self.revoked=True

    def attempt(self, intent: Intent, now: int, *, outcome: str = 'success') -> dict:
        with self._lock:
            p=self.policy
            integer(now,'now')
            if type(intent) is not Intent or outcome not in ('success','failure'):
                raise ValueError('invalid synthetic request')
            if self.revoked or not p.valid_from <= now < p.valid_until or now < self.last_time:
                raise ValueError('session revoked, expired or clock rollback')
            if intent.evidence_class != 'SYNTHETIC' or intent.action != 'swap':
                raise ValueError('only synthetic exact-input swaps')
            for name in ('chain_id','route','recipient','selector','token_in','token_out'):
                if type(getattr(intent,name)) is not type(getattr(p,name)) or getattr(intent,name) != getattr(p,name):
                    raise ValueError(f'policy mismatch: {name}')
            for name in ('amount_in_atomic','quoted_out_atomic','minimum_out_atomic','notional_micro_usd'):
                integer(getattr(intent,name),name,1)
            for name in ('fee_upper_micro_usd','observed_at','deadline','nonce'):
                integer(getattr(intent,name),name)
            if intent.nonce != self.next_nonce:
                raise ValueError('nonce replay or skipped sequence')
            if not (0 <= now-intent.observed_at <= p.max_quote_age_s and now <= intent.deadline < p.valid_until):
                raise ValueError('future, stale or expired quote')
            minimum=(intent.quoted_out_atomic*(10000-p.max_slippage_bps)+9999)//10000
            if not minimum <= intent.minimum_out_atomic <= intent.quoted_out_atomic:
                raise ValueError('minimum output violates quote/slippage bounds')
            if intent.notional_micro_usd > p.max_order_micro_usd:
                raise ValueError('order cap')
            if intent.fee_upper_micro_usd > p.max_fee_per_attempt_micro_usd:
                raise ValueError('per-attempt fee cap')
            fee_total=self.fees_reserved_micro_usd+intent.fee_upper_micro_usd
            if fee_total > p.total_fee_budget_micro_usd:
                raise ValueError('cumulative fee budget')
            if intent.notional_micro_usd+fee_total > p.initial_micro_usd-p.reserve_micro_usd:
                raise ValueError('reserve budget')
            recent=[a for a in self._attempts if now-a[0] < 86400]
            if len(recent) >= p.max_attempts_24h:
                raise ValueError('rolling attempt cap')
            if sum(a[1] for a in recent)+intent.notional_micro_usd > p.max_notional_24h_micro_usd:
                raise ValueError('rolling notional cap')
            total=self.lifetime_notional_micro_usd+intent.notional_micro_usd
            if total > p.lifetime_notional_micro_usd:
                raise ValueError('session cumulative notional cap')
            # Conservative reservation: even a simulated failure consumes the
            # submitted notional authorization and fee bound. Not realized PnL.
            self._attempts=recent+[(now,intent.notional_micro_usd)]
            self.last_time=now
            self.next_nonce+=1
            self.lifetime_notional_micro_usd=total
            self.fees_reserved_micro_usd=fee_total
            return {'status':f'MOCK_{outcome.upper()}_NOT_SIGNED',
                    'financial_signature':False,'nonce':intent.nonce,
                    'fees_reserved_micro_usd':fee_total,
                    'warning':'Policy-only simulation; no financial execution or loss guarantee.'}
