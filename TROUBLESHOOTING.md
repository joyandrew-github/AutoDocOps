# Troubleshooting Guide

Common issues and solutions for AutoDocOps v1.0.

## Database Issues

### Connection Refused

**Symptoms**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
- Verify PostgreSQL is running: `docker ps | grep postgres`
- Check `POSTGRES_SERVER`, `POSTGRES_PORT` in `.env`
- Ensure network connectivity (e.g., Docker network)
- Check PostgreSQL logs: `docker logs postgres`

### Migration Errors

**Symptoms**: `alembic.util.exc.CommandError: Target database is not up to date`

**Solutions**:
```bash
# Check current version
alembic current

# Reset to base (CAUTION: data loss)
alembic downgrade base
alembic upgrade head

# Or stamp head if schema matches
alembic stamp head
```

## Neo4j Issues

### Bolt Connection Failed

**Symptoms**: `ServiceUnavailable: Unable to connect to bolt://localhost:7687`

**Solutions**:
- Verify Neo4j is running: `docker ps | grep neo4j`
- Check `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` in `.env`
- Wait for Neo4j to fully start (can take 30+ seconds)
- Check Neo4j logs: `docker logs neo4j`

### Graph Sync Failures

**Symptoms**: Graph sync returns errors or no nodes created

**Solutions**:
- Ensure repository was parsed successfully first
- Check Neo4j has available memory
- Verify AST nodes exist in database
- Check parser logs for errors

## Redis Issues

### Connection Refused

**Symptoms**: `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solutions**:
- Verify Redis is running: `docker ps | grep redis`
- Check `REDIS_HOST`, `REDIS_PORT` in `.env`
- Test Redis CLI: `docker exec -it redis redis-cli ping`

### Celery Task Failures

**Symptoms**: Tasks not processing, stuck in queue

**Solutions**:
```bash
# Check Celery worker logs
docker logs celery-worker

# Purge queue (CAUTION: data loss)
docker exec -it celery celery -A app.celery_app purge -f

# Restart worker
docker-compose restart celery-worker
```

## API Issues

### 401 Unauthorized

**Symptoms**: `401 Unauthorized` on API calls

**Solutions**:
- Verify JWT token is not expired
- Check `SECRET_KEY` matches between services
- Ensure user is active: `SELECT * FROM users WHERE is_active = true`
- Refresh token if using refresh flow

### 422 Validation Error

**Symptoms**: `422 Unprocessable Entity` on POST/PUT

**Solutions**:
- Check request body matches Pydantic schema
- Verify required fields are present
- Check data types (strings vs numbers)
- Review API docs: `http://localhost:8000/api/docs`

### 500 Internal Server Error

**Symptoms**: Generic 500 error

**Solutions**:
- Check backend logs: `docker logs backend`
- Enable debug mode temporarily: `DEBUG=true`
- Check database connection pool size
- Verify all dependencies are installed

## Frontend Issues

### Build Failures

**Symptoms**: `npm run build` fails

**Solutions**:
```bash
# Clear cache
rm -rf node_modules/.cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules
npm install

# Check Node.js version
node --version  # Should be 20+
```

### API Connection Errors

**Symptoms**: Frontend shows "Failed to fetch" errors

**Solutions**:
- Verify backend is running: `curl http://localhost:8000/api/v1/health`
- Check `NEXT_PUBLIC_API_URL` in frontend `.env.local`
- Verify CORS origins in backend config
- Check browser console for CORS errors

### White Screen / Runtime Errors

**Symptoms**: Blank page or React errors

**Solutions**:
- Check browser console for errors
- Verify API responses are valid JSON
- Check for missing environment variables
- Clear browser cache and localStorage

## Integration Issues

### Jira Connection Failed

**Symptoms**: Jira sync returns 401 or connection error

**Solutions**:
- Verify API token is valid (Atlassian account settings)
- Check base URL format: `https://myorg.atlassian.net`
- Ensure user has API access permissions
- Test with curl: `curl -u email:token https://myorg.atlassian.net/rest/api/3/myself`

### Slack Webhook Not Delivering

**Symptoms**: Slack notifications not received

**Solutions**:
- Verify webhook URL is correct
- Check webhook is enabled in Slack app
- Test webhook with curl
- Check rate limits (Slack has limits per workspace)

### GitLab PAT Issues

**Symptoms**: GitLab sync returns 401

**Solutions**:
- Verify PAT has `api` scope
- Check PAT is not expired
- Test with curl: `curl -H "PRIVATE-TOKEN: token" https://gitlab.com/api/v4/user`

## Performance Issues

### Slow API Responses

**Symptoms**: API calls take >5 seconds

**Solutions**:
- Enable query logging to identify slow queries
- Add database indexes on frequently queried columns
- Increase database connection pool size
- Check for N+1 query patterns
- Use pagination for large result sets

### High Memory Usage

**Symptoms**: Container OOM killed or high RAM usage

**Solutions**:
- Increase container memory limits
- Reduce batch sizes (e.g., embedding batch size)
- Enable Redis caching where applicable
- Check for memory leaks in long-running processes
- Profile with `memory_profiler`

### Frontend Bundle Size

**Symptoms**: Large initial bundle (>2MB)

**Solutions**:
- Enable dynamic imports for code splitting
- Use tree-shaking for unused exports
- Optimize images and assets
- Enable gzip compression on web server
- Consider CDN for static assets

## Logging Issues

### Logs Not Appearing

**Symptoms**: Expected log messages missing

**Solutions**:
- Verify `LOG_LEVEL` is set appropriately (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- Check log file permissions
- Ensure logger is imported: `from app.core.logging import get_logger`
- Check if log aggregation is configured

## Getting Help

If issues persist:
1. Check [GitHub Issues](https://github.com/yourorg/autodocops/issues)
2. Review [Deployment Guide](DEPLOYMENT.md)
3. Enable debug mode and collect logs
4. Provide environment details (OS, versions, config)
