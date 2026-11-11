let route2 = null;
        let headersOverride;
        if (requestPausedEvent) {
          if (redirectedFrom || !this._userRequestInterceptionEnabled && this._protocolRequestInterceptionEnabled) {
            headersOverride = redirectedFrom?._originalRequestRoute?._alreadyContinuedParams?.headers;
            if (headersOverride) {
              const originalHeaders = Object.entries(requestPausedEvent.request.headers).map(([name, value2]) => ({ name, value: value2 }));
              headersOverride = removeCookieHeader(applyHeadersOverrides(originalHeaders, headersOverride));
            }
            requestPausedSessionInfo.session._sendMayFail("Fetch.continueRequest", { requestId: requestPausedEvent.requestId, headers: headersOverride });
          } else {
            route2 = new RouteImpl(requestPausedSessionInfo.session, requestPausedEvent.requestId);
          }
        }
        