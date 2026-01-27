# URGENT FIX GUIDE - Bidding Not Working

## Run These Commands NOW

### 1. Check Django Server Logs
The Django server will now print detailed logs when bids are placed. Watch for:
```
====================================================
PLACE BID REQUEST
====================================================
Team: MI
Amount: 35
====================================================

Current Room State:
  Current Bid: 30
  Highest Bidder: DC
  Player: Abhinav Manohar
  Team Budget: ₹120 Cr (₹12000000L)
  Bid Amount: ₹35L
  ✅ Bid accepted! New bid: ₹35L by MI
====================================================
```

### 2. Check Browser Console (F12)
Open browser console and look for:
- Any JavaScript errors
- "Bid accepted" or error messages
- Network requests to `/api/place-bid/`

### 3. Test Bid Flow

**User 1 (Team DC)**:
1. Click "PLACE BID (30L)" → Should succeed
2. Current bid should change to ₹30L
3. Highest bidder should show "DC"

**User 2 (Team MI)**:
1. Button should now show "PLACE BID (35L)" ← **Check this!**
2. Click button → Should succeed
3. Current bid should change to ₹35L
4. Highest bidder should show "MI"

**User 1 tries again**:
1. Button should show "PLACE BID (40L)"
2. Click → Should succeed
3. Current bid → ₹40L

---

## If Bids Still Not Working

### Check 1: Frontend is Sending Correct Amount

Add this to browser console:
```javascript
// Check what amount button is sending
const button = document.querySelector('[style*="PLACE BID"]');
console.log('Button text:', button?.textContent);
```

### Check 2: API Response

In browser Network tab:
1. Click "PLACE BID"
2. Find `/api/place-bid/` request
3. Check Request Payload:
   ```json
   {
     "code": "U7LI",
     "team": "MI",
     "amount": 35  ← Should be NUMBER not string!
   }
   ```
4. Check Response:
   - Status 200 = Success
   - Status 403 = "You already have highest bid" or budget issue

### Check 3: Room State Updates

Check `/api/room-state/` responses:
- `current_bid` should increase after each bid
- `highest_bidder` should change between teams
- `bid_increment` should be 5, 10, or 20 based on current bid

---

## Common Issues

### Issue: "You already have highest bid"
**Cause**: Same team trying to bid twice  
**Solution**: Use DIFFERENT team/browser to bid

### Issue: Bid amount shows as string "30L" instead of number 30
**Cause**: Frontend sending formatted string  
**Fix**: Check `placeBid()` function - should send NUMBER

### Issue: Current bid not updating in UI
**Cause**: State sync not working  
**Check**: `/api/room-state/` polling interval (should be 1000ms)

---

## SOLD Display Issue

When timer hits 0:
1. Backend creates Auction record (check database)
2. Frontend detects `timer === 0`
3. Sets `soldStatus` state
4. Replaces bid display with SOLD

**Debug**:
```javascript
// In browser console during auction
setInterval(() => {
  console.log('Timer:', document.querySelector('[style*="font-size: 32px"]')?.textContent);
}, 1000);
```

When timer shows "0s":
- Check console for "SOLD" state change
- Should see green "SOLD!" text replace bid amount

---

## Purse Deduction

After player is sold:
1. Backend deducts from `participant.budget` (line 301 in views.py)
2. Frontend fetches via `/api/room-state/?team=MI`
3. Should see `user_budget` decrease

**Check**:
1. Initial budget: ₹120 Cr
2. Buy player for ₹220L (₹2.20 Cr)
3. New budget: ₹117.80 Cr

---

## RESTART Django Server

After adding logging, restart server:
```bash
# Stop with Ctrl+C, then:
python manage.py runserver
```

Then test again and **watch the Django console output** when clicking PLACE BID!
