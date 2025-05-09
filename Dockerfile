FROM public.ecr.aws/lambda/python:3.10

# Copy source code
COPY src/ ${LAMBDA_TASK_ROOT}/src/

# Copy requirements and test scripts
COPY requirements.txt lambda_entry.py ${LAMBDA_TASK_ROOT}/

# Install uv (fast Python package manager)
RUN pip install --no-cache-dir uv
RUN uv venv /opt/venv
# Use the virtual environment automatically
ENV VIRTUAL_ENV=/opt/venv
# Place entry points in the environment at the front of the path
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies using uv
RUN uv pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt

ENV PYTHONPATH=${LAMBDA_TASK_ROOT}

# Set the handler
CMD [ "src.lambda_functions.document_processor.app.handler" ] 