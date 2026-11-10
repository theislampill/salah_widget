        if args.expect == 'withdrawal':
            refresh_observations = [observation for observation in row['observations']
                if recovered['elapsedMs'] <= observation['state']['elapsedMs'] <= final['elapsedMs']]
            refresh_evidence = healthy_refresh_evidence(recovered, final, fixture['passive'],
                [observation['state'] for observation in refresh_observations], fixture['ledger'], args.mode)
            refresh_trace_path = out / 'healthy-refresh-passive.json'
            dump(refresh_trace_path, [sample for sample in fixture['passive']
                if recovered['elapsedMs'] <= sample['elapsedMs'] <= final['elapsedMs']])
            refresh_evidence['retainedFullCaptures'] = [{'stage': observation['stage'],
                'file': observation['stage'] + '.json', 'artifacts': observation['artifacts']}
                for observation in refresh_observations]
            refresh_evidence['passiveTrace'] = {'file': refresh_trace_path.name, 'sha256': sha(refresh_trace_path.read_bytes())}
            row['healthyRefreshEvidence'] = refresh_evidence
            row['checks'].update({'healthyRefresh/' + name: passed for name, passed in refresh_evidence['checks'].items()})
            row['checks']['healthyRefreshContinuity'] = refresh_evidence['ok']
            dump(out / 'healthy-refresh-evidence.json', refresh_evidence)

