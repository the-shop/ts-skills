import assert from 'node:assert/strict';
import { checkout } from './checkout.mjs';
assert.deepEqual(checkout(3.99, 3), { cents: 1197, display: 'USD 11.97' });
assert.equal(checkout(3.99, 1).cents, 399);
assert.equal(checkout(3.99, 0).cents, 0);
console.log('checkout: 3 checks passed');
