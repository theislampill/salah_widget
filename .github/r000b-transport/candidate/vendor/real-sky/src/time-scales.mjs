/** Time policy: USNO TAI-UTC table, IERS Bulletin C72 (2026-07-06), NASA historical DeltaT.
 * See docs/CHECKPOINT_4.md. Numeric POSIX milliseconds cannot represent a leap-second label.
 * No host clock or time zone is read. Future offsets are explicitly uncertain, not predicted.
 */
const TS_DAY=86400000;
const TS_LEAPS=[[1972,1,10],[1972,7,11],[1973,1,12],[1974,1,13],[1975,1,14],[1976,1,15],[1977,1,16],[1978,1,17],[1979,1,18],[1980,1,19],[1981,7,20],[1982,7,21],[1983,7,22],[1985,7,23],[1988,1,24],[1990,1,25],[1991,1,26],[1992,7,27],[1993,7,28],[1994,7,29],[1996,1,30],[1997,7,31],[1999,1,32],[2006,1,33],[2009,1,34],[2012,7,35],[2015,7,36],[2017,1,37]].map(([y,m,n])=>[Date.UTC(y,m-1,1),n]);
const TS_DRIFTS=[[1961,1,1.422818,37300,.001296],[1961,8,1.372818,37300,.001296],[1962,1,1.845858,37665,.0011232],[1963,11,1.945858,37665,.0011232],[1964,1,3.240130,38761,.001296],[1964,4,3.340130,38761,.001296],[1964,9,3.440130,38761,.001296],[1965,1,3.540130,38761,.001296],[1965,3,3.640130,38761,.001296],[1965,7,3.740130,38761,.001296],[1965,9,3.840130,38761,.001296],[1966,1,4.313170,39126,.002592],[1968,2,4.213170,39126,.002592]].map(([y,m,a,b,c])=>[Date.UTC(y,m-1,1),a,b,c]);
function tsNumber(x,label,min=-Infinity,max=Infinity){if(typeof x!=='number'||!Number.isFinite(x)||x<min||x>max)throw new RangeError(label+' out of range');return x;}
function historicDeltaT(y){let t;if(y<1920){t=y-1900;return -2.79+1.494119*t-.0598939*t*t+.0061966*t**3-.000197*t**4;}if(y<1941){t=y-1920;return 21.2+.84493*t-.0761*t*t+.0020936*t**3;}t=y-1950;return 29.07+.407*t-t*t/233+t**3/2547;}
export function timeScales(observer){
 const ms=tsNumber(observer.utcMs,'UTC milliseconds'),date=new Date(ms),year=date.getUTCFullYear();
 if(!Number.isFinite(year)||year<1900||year>2100)throw new RangeError('supported dates: Gregorian1900–2100');
 const jdUtc=ms/TS_DAY+2440587.5,dut1=tsNumber(observer.dut1Seconds??0,'UT1-UTC',-1,1),warnings=[];let offset;
 if(observer.dut1Seconds==null)warnings.push('UT1-assumed-UTC');
 if(observer.ttMinusUtcSeconds!=null)offset=tsNumber(observer.ttMinusUtcSeconds,'TT-UTC',-200,1000);
 else if(ms>=TS_LEAPS[0][0]){offset=32.184+TS_LEAPS.filter(r=>r[0]<=ms).at(-1)[1];if(ms>=Date.UTC(2027,0,1))warnings.push('future-TAI-UTC-assumed-last-confirmed');}
 else if(ms>=TS_DRIFTS[0][0]){const r=TS_DRIFTS.filter(r=>r[0]<=ms).at(-1);offset=32.184+r[1]+(jdUtc-2400000.5-r[2])*r[3];}
 else{offset=historicDeltaT(year+(date.getUTCMonth()+.5)/12)+dut1;warnings.push('pre1961-proleptic-time-with-estimated-deltaT');}
 return {jdUtc,jdUt1:jdUtc+dut1/86400,jdTt:jdUtc+offset/86400,dut1Seconds:dut1,ttMinusUtcSeconds:offset,warnings};
}
