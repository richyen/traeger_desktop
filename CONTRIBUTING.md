# Contributing to Traeger Controller

Thank you for your interest in contributing! This project was reverse-engineered from the Traeger mobile app API, and there's still much to discover.

## How to Contribute

### Discovering New API Endpoints

If you find new API endpoints or commands:

1. **Capture traffic** with mitmproxy while using different features in the Traeger app
2. **Document your findings** - what feature triggered it? What parameters does it accept?
3. **Add to `traeger_client.py`** - implement the new functionality
4. **Update documentation** - add examples to README or QUICKSTART
5. **Submit a pull request**

### Code Style

- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Include type hints where possible
- Keep functions focused and single-purpose

### Testing

- Test with actual hardware when possible
- Document any quirks or edge cases you discover
- Note which grill models you've tested with

### Areas Needing Help

- **Real-time MQTT Implementation** - Full bidirectional MQTT support
- **GraphQL Endpoints** - Recipe management, cook history, social features
- **OAuth Implementation** - Proper Cognito authentication flow
- **Error Handling** - Better error messages and recovery
- **Documentation** - More examples, troubleshooting tips
- **Platform Support** - Testing on Windows, Linux, different grill models

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/traeger-controller.git
cd traeger-controller

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .
pip install -r requirements.txt

# Capture your token (see SETUP.md)
python extract_token.py
```

## Submitting Changes

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-api-endpoint`
3. **Make your changes** and commit with clear messages
4. **Test thoroughly** with real hardware if possible
5. **Update documentation** as needed
6. **Submit a pull request** with a description of what you've added

## API Discovery Tips

### Finding Endpoints
- Use mitmproxy's search feature to filter Traeger domains
- Look for patterns in URL paths and command formats
- Check GraphQL queries in request bodies
- Note HTTP methods (GET, POST, PUT, DELETE)

### Understanding Commands
- Grill commands use simple comma-separated formats
- Temperature values are in Fahrenheit
- Probe IDs are usually 0-3 (p0, p1, p2, p3)
- Some commands return responses, others just 200 OK

### Common Patterns
```python
# Temperature setting
"112,<temp>"

# Probe alarm
"120,10,p<probe_id>,<temp>"

# Status request
"113"

# Power control
"90,<0|1>"
```

### GraphQL Queries
Look for POST requests to `api.kube-gql.prod.traegergrills.io`:
- Request body contains `query` and `variables`
- Use GraphQL introspection to discover schema
- Many queries have fragments defined inline

## Reporting Issues

When reporting bugs or issues:

- Include your Python version
- Describe your grill model
- Share relevant error messages
- Note what you were trying to do
- **Never** include your actual auth token in issues

## Security & Privacy

- **Never commit tokens or credentials** to the repository
- Use `traeger_config.example.json` for examples
- Anonymize any personal data in documentation
- Report security issues privately to maintainers

## Questions?

- Check existing issues and pull requests
- Review [AUTHENTICATION_ANALYSIS.md](AUTHENTICATION_ANALYSIS.md) for technical details
- Open a discussion for general questions
- Be patient - this is a community project!

## Code of Conduct

- Be respectful and inclusive
- Help others learn
- Give constructive feedback
- Remember: we're all here to make better BBQ! 🍖

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
