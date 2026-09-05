import { subtotal } from './pricing.mjs';
export function checkout(unitDollars, quantity) {
  const cents = subtotal(unitDollars, quantity);
  return { cents, display: `USD ${(cents / 100).toFixed(2)}` };
}
console.log(JSON.stringify(checkout(3.99, 3)));
