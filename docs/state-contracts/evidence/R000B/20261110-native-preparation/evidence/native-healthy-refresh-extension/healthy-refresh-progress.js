const readHealthyRefreshProgress = () => {
  const f=window.__withdrawalFixture;
  if(f?.state==='error')throw Error(f.error);
  if(f?.state!=='ready')throw Error('Expected the existing ready fixture');
  return {elapsedMs:performance.now()-f.started,maxElapsedMs:f.maxElapsedMs,
          latest:f.latest,ledger:f.ledger.filter(request=>request.kind==='weather')};
};
