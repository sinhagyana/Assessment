import os

from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Document
from .serializers import (
    DocumentDetailSerializer,
    DocumentListSerializer,
    DocumentUploadSerializer,
)
from .services import process_document


class DocumentUploadView(APIView):

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        upload = request.FILES.get("file")
        if not upload:
            return Response(
                {"error": {"message": "No file provided.", "detail": "Field 'file' is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ext = os.path.splitext(upload.name)[1].lower()
        document = Document.objects.create(
            file=upload,
            original_filename=upload.name,
            file_type=ext,
            file_size=upload.size,
        )

        document = process_document(document)

        response_serializer = DocumentDetailSerializer(
            document, context={"request": request}
        )
        response_status = (
            status.HTTP_201_CREATED
            if document.status == Document.Status.COMPLETED
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        return Response(response_serializer.data, status=response_status)


class DocumentListView(ListAPIView):

    serializer_class = DocumentListSerializer

    def get_queryset(self):
        queryset = Document.objects.all()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset


class DocumentDetailView(RetrieveAPIView):

    queryset = Document.objects.all()
    serializer_class = DocumentDetailSerializer
    lookup_field = "id"
