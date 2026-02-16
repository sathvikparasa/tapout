package com.warnabrotha.app.ui.screens

import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CameraAlt
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.ErrorOutline
import androidx.compose.material.icons.outlined.PhotoLibrary
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.warnabrotha.app.data.model.TicketScanResponse
import com.warnabrotha.app.ui.theme.*
import com.warnabrotha.app.ui.viewmodel.ScanState

@Composable
fun ScanTab(
    scanState: ScanState,
    scanImageUri: Uri?,
    scanResult: TicketScanResponse?,
    scanError: String?,
    isLoading: Boolean,
    onTakePhoto: () -> Unit,
    onPickFromLibrary: () -> Unit,
    onSubmitScan: () -> Unit,
    onResetScan: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(Background)
            .padding(horizontal = 20.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        when (scanState) {
            ScanState.IDLE -> IdleContent(
                onTakePhoto = onTakePhoto,
                onPickFromLibrary = onPickFromLibrary
            )
            ScanState.PREVIEW -> PreviewContent(
                imageUri = scanImageUri,
                onSubmit = onSubmitScan,
                onRetake = onResetScan
            )
            ScanState.PROCESSING -> ProcessingContent()
            ScanState.SUCCESS -> SuccessContent(
                result = scanResult,
                onScanAnother = onResetScan
            )
            ScanState.ERROR -> ErrorContent(
                error = scanError,
                onTryAgain = onResetScan
            )
        }
    }
}

@Composable
private fun IdleContent(
    onTakePhoto: () -> Unit,
    onPickFromLibrary: () -> Unit
) {
    Spacer(modifier = Modifier.height(80.dp))

    // Camera icon circle
    Box(
        modifier = Modifier
            .size(120.dp)
            .clip(CircleShape)
            .background(GreenOverlay10)
            .border(2.dp, Green500, CircleShape),
        contentAlignment = Alignment.Center
    ) {
        Icon(
            imageVector = Icons.Outlined.CameraAlt,
            contentDescription = "Camera",
            tint = Green500,
            modifier = Modifier.size(48.dp)
        )
    }

    Spacer(modifier = Modifier.height(24.dp))

    Text(
        text = "Scan a Ticket",
        style = MaterialTheme.typography.displayMedium.copy(
            fontFamily = DmSansFamily,
            fontWeight = FontWeight.ExtraBold,
            letterSpacing = (-0.75).sp
        ),
        color = TextPrimary
    )

    Spacer(modifier = Modifier.height(8.dp))

    Text(
        text = "Take a photo of your parking ticket to auto-report TAPS",
        style = MaterialTheme.typography.bodyMedium,
        color = TextSecondary,
        textAlign = TextAlign.Center,
        modifier = Modifier.padding(horizontal = 20.dp)
    )

    Spacer(modifier = Modifier.height(40.dp))

    // Take Photo button
    Button(
        onClick = onTakePhoto,
        modifier = Modifier
            .fillMaxWidth()
            .height(56.dp),
        shape = RoundedCornerShape(24.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = Green500,
            contentColor = TextOnPrimary
        )
    ) {
        Icon(
            imageVector = Icons.Outlined.CameraAlt,
            contentDescription = null,
            modifier = Modifier.size(20.dp)
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = "Take Photo",
            style = MaterialTheme.typography.labelLarge.copy(
                fontFamily = DmSansFamily,
                fontWeight = FontWeight.Bold
            )
        )
    }

    Spacer(modifier = Modifier.height(12.dp))

    // Choose from Library button
    OutlinedButton(
        onClick = onPickFromLibrary,
        modifier = Modifier
            .fillMaxWidth()
            .height(56.dp),
        shape = RoundedCornerShape(24.dp),
        colors = ButtonDefaults.outlinedButtonColors(
            contentColor = Green500
        ),
        border = androidx.compose.foundation.BorderStroke(1.5.dp, Green500)
    ) {
        Icon(
            imageVector = Icons.Outlined.PhotoLibrary,
            contentDescription = null,
            modifier = Modifier.size(20.dp)
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = "Choose from Library",
            style = MaterialTheme.typography.labelLarge.copy(
                fontFamily = DmSansFamily,
                fontWeight = FontWeight.Bold
            )
        )
    }
}

@Composable
private fun PreviewContent(
    imageUri: Uri?,
    onSubmit: () -> Unit,
    onRetake: () -> Unit
) {
    Spacer(modifier = Modifier.height(32.dp))

    Text(
        text = "Preview",
        style = MaterialTheme.typography.headlineLarge,
        color = TextPrimary
    )

    Spacer(modifier = Modifier.height(16.dp))

    // Image preview
    if (imageUri != null) {
        AsyncImage(
            model = ImageRequest.Builder(LocalContext.current)
                .data(imageUri)
                .crossfade(true)
                .build(),
            contentDescription = "Ticket preview",
            modifier = Modifier
                .fillMaxWidth()
                .height(300.dp)
                .clip(RoundedCornerShape(16.dp))
                .border(1.dp, Border, RoundedCornerShape(16.dp)),
            contentScale = ContentScale.Fit
        )
    }

    Spacer(modifier = Modifier.height(24.dp))

    // Submit button
    Button(
        onClick = onSubmit,
        modifier = Modifier
            .fillMaxWidth()
            .height(56.dp),
        shape = RoundedCornerShape(24.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = Green500,
            contentColor = TextOnPrimary
        )
    ) {
        Text(
            text = "Submit Ticket",
            style = MaterialTheme.typography.labelLarge.copy(
                fontFamily = DmSansFamily,
                fontWeight = FontWeight.Bold
            )
        )
    }

    Spacer(modifier = Modifier.height(12.dp))

    // Retake button
    TextButton(
        onClick = onRetake,
        modifier = Modifier.fillMaxWidth()
    ) {
        Text(
            text = "Retake",
            style = MaterialTheme.typography.labelLarge,
            color = TextSecondary
        )
    }
}

@Composable
private fun ProcessingContent() {
    Spacer(modifier = Modifier.weight(1f))

    CircularProgressIndicator(
        color = Green500,
        modifier = Modifier.size(48.dp),
        strokeWidth = 4.dp
    )

    Spacer(modifier = Modifier.height(24.dp))

    Text(
        text = "Reading ticket...",
        style = MaterialTheme.typography.headlineMedium,
        color = TextPrimary
    )

    Spacer(modifier = Modifier.height(8.dp))

    Text(
        text = "Extracting date, time, and location",
        style = MaterialTheme.typography.bodyMedium,
        color = TextSecondary
    )

    Spacer(modifier = Modifier.weight(1f))
}

@Composable
private fun SuccessContent(
    result: TicketScanResponse?,
    onScanAnother: () -> Unit
) {
    Spacer(modifier = Modifier.height(48.dp))

    // Success icon
    Box(
        modifier = Modifier
            .size(80.dp)
            .clip(CircleShape)
            .background(GreenOverlay10),
        contentAlignment = Alignment.Center
    ) {
        Icon(
            imageVector = Icons.Outlined.CheckCircle,
            contentDescription = "Success",
            tint = Green500,
            modifier = Modifier.size(48.dp)
        )
    }

    Spacer(modifier = Modifier.height(24.dp))

    if (result != null) {
        // Extracted data card
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            color = Surface,
            border = androidx.compose.foundation.BorderStroke(1.dp, Border)
        ) {
            Column(modifier = Modifier.padding(20.dp)) {
                Text(
                    text = "Ticket Details",
                    style = MaterialTheme.typography.headlineSmall,
                    color = TextPrimary
                )

                Spacer(modifier = Modifier.height(12.dp))

                result.ticketDate?.let { date ->
                    DetailRow(label = "Date", value = date)
                }
                result.ticketTime?.let { time ->
                    DetailRow(label = "Time", value = time)
                }
                result.ticketLocation?.let { location ->
                    DetailRow(label = "Location", value = location)
                }
                result.mappedLotName?.let { lotName ->
                    DetailRow(label = "Mapped to", value = lotName)
                }
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Result message
        if (result.isRecent && result.sightingId != null) {
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                color = GreenOverlay10
            ) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "TAPS report created!",
                        style = MaterialTheme.typography.headlineSmall,
                        color = Green600
                    )
                    Text(
                        text = "${result.usersNotified} users notified",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Green600
                    )
                }
            }
        } else if (result.sightingId != null) {
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                color = CardBackgroundMuted
            ) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "Ticket recorded",
                        style = MaterialTheme.typography.headlineSmall,
                        color = TextPrimary
                    )
                    Text(
                        text = "Too old for a live report",
                        style = MaterialTheme.typography.bodyMedium,
                        color = TextSecondary
                    )
                }
            }
        } else if (result.mappedLotId == null && result.ticketLocation != null) {
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                color = RedOverlay10
            ) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "Location not recognized",
                        style = MaterialTheme.typography.headlineSmall,
                        color = Red500
                    )
                    Text(
                        text = "Couldn't create a report for this location",
                        style = MaterialTheme.typography.bodyMedium,
                        color = TextSecondary
                    )
                }
            }
        }
    }

    Spacer(modifier = Modifier.height(32.dp))

    Button(
        onClick = onScanAnother,
        modifier = Modifier
            .fillMaxWidth()
            .height(56.dp),
        shape = RoundedCornerShape(24.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = Green500,
            contentColor = TextOnPrimary
        )
    ) {
        Text(
            text = "Scan Another",
            style = MaterialTheme.typography.labelLarge.copy(
                fontFamily = DmSansFamily,
                fontWeight = FontWeight.Bold
            )
        )
    }
}

@Composable
private fun DetailRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            color = TextSecondary
        )
        Text(
            text = value,
            style = MaterialTheme.typography.titleMedium,
            color = TextPrimary
        )
    }
}

@Composable
private fun ErrorContent(
    error: String?,
    onTryAgain: () -> Unit
) {
    Spacer(modifier = Modifier.weight(1f))

    // Error icon
    Box(
        modifier = Modifier
            .size(80.dp)
            .clip(CircleShape)
            .background(RedOverlay10),
        contentAlignment = Alignment.Center
    ) {
        Icon(
            imageVector = Icons.Outlined.ErrorOutline,
            contentDescription = "Error",
            tint = Red500,
            modifier = Modifier.size(48.dp)
        )
    }

    Spacer(modifier = Modifier.height(24.dp))

    Text(
        text = "Could not read ticket",
        style = MaterialTheme.typography.headlineLarge,
        color = TextPrimary,
        textAlign = TextAlign.Center
    )

    Spacer(modifier = Modifier.height(8.dp))

    Text(
        text = error ?: "Make sure the photo is clear and shows a UC Davis parking ticket.",
        style = MaterialTheme.typography.bodyMedium,
        color = TextSecondary,
        textAlign = TextAlign.Center,
        modifier = Modifier.padding(horizontal = 20.dp)
    )

    Spacer(modifier = Modifier.height(32.dp))

    Button(
        onClick = onTryAgain,
        modifier = Modifier
            .fillMaxWidth()
            .height(56.dp),
        shape = RoundedCornerShape(24.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = Green500,
            contentColor = TextOnPrimary
        )
    ) {
        Text(
            text = "Try Again",
            style = MaterialTheme.typography.labelLarge.copy(
                fontFamily = DmSansFamily,
                fontWeight = FontWeight.Bold
            )
        )
    }

    Spacer(modifier = Modifier.weight(1f))
}
