package com.warnabrotha.app.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.DirectionsCar
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.google.android.gms.maps.model.BitmapDescriptorFactory
import com.google.android.gms.maps.model.CameraPosition
import com.google.android.gms.maps.model.LatLng
import com.google.android.gms.maps.model.MapStyleOptions
import com.google.maps.android.compose.*
import com.warnabrotha.app.data.model.ParkingLot
import com.warnabrotha.app.data.model.ParkingLotWithStats
import com.warnabrotha.app.data.model.ParkingSession
import com.warnabrotha.app.ui.theme.*

// UC Davis campus center coordinates (centered between all three lots)
private val UC_DAVIS_CENTER = LatLng(38.5422, -121.7551)
private const val DEFAULT_ZOOM = 15.5f

// Hardcoded parking lot coordinates
private val PARKING_LOT_COORDINATES = mapOf(
    "MU" to LatLng(38.544416, -121.749561),       // Quad Parking Structure
    "HUTCH" to LatLng(38.53969, -121.758182),     // Pavilion Structure
    "ARC" to LatLng(38.54304, -121.757572)        // Lot 25
)

@Composable
fun MapTab(
    parkingLots: List<ParkingLot>,
    lotStats: Map<Int, ParkingLotWithStats>,
    currentSession: ParkingSession?,
    isLoading: Boolean,
    onCheckIn: (Int) -> Unit,
    onCheckOut: () -> Unit,
    onReportTaps: (Int) -> Unit,
    modifier: Modifier = Modifier
) {
    var selectedLot by remember { mutableStateOf<ParkingLot?>(null) }

    val cameraPositionState = rememberCameraPositionState {
        position = CameraPosition.fromLatLngZoom(UC_DAVIS_CENTER, DEFAULT_ZOOM)
    }

    val mapProperties = remember {
        MapProperties(
            mapType = MapType.NORMAL,
            isMyLocationEnabled = false,
            mapStyleOptions = MapStyleOptions(hidePoiMapStyle)
        )
    }

    val mapUiSettings = remember {
        MapUiSettings(
            zoomControlsEnabled = true,
            compassEnabled = true,
            mapToolbarEnabled = false,
            myLocationButtonEnabled = false,
            rotationGesturesEnabled = true,
            scrollGesturesEnabled = true,
            tiltGesturesEnabled = true,
            zoomGesturesEnabled = true
        )
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Black900)
    ) {
        // Header overlay
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp)
                .statusBarsPadding()
        ) {
            Text(
                text = "CAMPUS MAP",
                style = MaterialTheme.typography.labelSmall,
                color = TextMuted,
                letterSpacing = 1.sp
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "Parking Lots",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = TextWhite
            )
        }

        // Map
        GoogleMap(
            modifier = Modifier
                .fillMaxSize()
                .padding(top = 80.dp),
            cameraPositionState = cameraPositionState,
            properties = mapProperties,
            uiSettings = mapUiSettings,
            onMapClick = { selectedLot = null }
        ) {
            // Add parking lot markers using hardcoded coordinates
            parkingLots.forEach { lot ->
                val coordinates = PARKING_LOT_COORDINATES[lot.code]
                if (coordinates != null) {
                    val isCheckedInHere = currentSession?.parkingLotId == lot.id
                    Marker(
                        state = MarkerState(position = coordinates),
                        title = lot.name,
                        snippet = lot.code,
                        icon = BitmapDescriptorFactory.defaultMarker(
                            if (isCheckedInHere) BitmapDescriptorFactory.HUE_GREEN
                            else BitmapDescriptorFactory.HUE_ORANGE
                        ),
                        onClick = {
                            selectedLot = lot
                            true
                        }
                    )
                }
            }
        }

        // Legend overlay at bottom (hidden when lot is selected)
        AnimatedVisibility(
            visible = selectedLot == null,
            enter = slideInVertically { it },
            exit = slideOutVertically { it },
            modifier = Modifier.align(Alignment.BottomCenter)
        ) {
            Box(
                modifier = Modifier
                    .padding(16.dp)
                    .padding(bottom = 8.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(Black800.copy(alpha = 0.95f))
                    .padding(horizontal = 16.dp, vertical = 12.dp)
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .size(12.dp)
                            .clip(RoundedCornerShape(2.dp))
                            .background(Amber500)
                    )
                    Text(
                        text = "Parking Lots",
                        style = MaterialTheme.typography.labelMedium,
                        color = TextGray
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "${parkingLots.count { PARKING_LOT_COORDINATES.containsKey(it.code) }} locations",
                        style = MaterialTheme.typography.labelSmall,
                        color = TextMuted
                    )
                }
            }
        }

        // Lot details bottom sheet
        AnimatedVisibility(
            visible = selectedLot != null,
            enter = slideInVertically { it },
            exit = slideOutVertically { it },
            modifier = Modifier.align(Alignment.BottomCenter)
        ) {
            selectedLot?.let { lot ->
                val stats = lotStats[lot.id]
                val isCheckedInHere = currentSession?.parkingLotId == lot.id
                val isCheckedInElsewhere = currentSession != null && currentSession.parkingLotId != lot.id

                LotDetailsSheet(
                    lot = lot,
                    stats = stats,
                    isCheckedInHere = isCheckedInHere,
                    isCheckedInElsewhere = isCheckedInElsewhere,
                    checkedInLotCode = currentSession?.parkingLotCode,
                    isLoading = isLoading,
                    onCheckIn = { onCheckIn(lot.id) },
                    onCheckOut = onCheckOut,
                    onReportTaps = { onReportTaps(lot.id) },
                    onDismiss = { selectedLot = null }
                )
            }
        }
    }
}

@Composable
private fun LotDetailsSheet(
    lot: ParkingLot,
    stats: ParkingLotWithStats?,
    isCheckedInHere: Boolean,
    isCheckedInElsewhere: Boolean,
    checkedInLotCode: String?,
    isLoading: Boolean,
    onCheckIn: () -> Unit,
    onCheckOut: () -> Unit,
    onReportTaps: () -> Unit,
    onDismiss: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(topStart = 20.dp, topEnd = 20.dp))
            .background(Black800)
            .padding(20.dp)
            .navigationBarsPadding()
    ) {
        // Header with close button
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = lot.code,
                    style = MaterialTheme.typography.labelSmall,
                    color = Amber500,
                    letterSpacing = 1.sp
                )
                Text(
                    text = lot.name,
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    color = TextWhite
                )
            }
            IconButton(
                onClick = onDismiss,
                modifier = Modifier
                    .size(32.dp)
                    .clip(CircleShape)
                    .background(Black700)
            ) {
                Icon(
                    imageVector = Icons.Default.Close,
                    contentDescription = "Close",
                    tint = TextMuted,
                    modifier = Modifier.size(18.dp)
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Stats row
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            StatCard(
                label = "PARKED",
                value = "${stats?.activeParkers ?: 0}",
                icon = Icons.Default.DirectionsCar,
                color = Blue500,
                modifier = Modifier.weight(1f)
            )
            StatCard(
                label = "REPORTS",
                value = "${stats?.recentSightings ?: 0}",
                icon = Icons.Default.Warning,
                color = if ((stats?.recentSightings ?: 0) > 0) Red500 else TextMuted,
                modifier = Modifier.weight(1f)
            )
        }

        // Checked in elsewhere warning
        if (isCheckedInElsewhere) {
            Spacer(modifier = Modifier.height(12.dp))
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(8.dp))
                    .background(Amber500.copy(alpha = 0.15f))
                    .border(1.dp, Amber500.copy(alpha = 0.3f), RoundedCornerShape(8.dp))
                    .padding(12.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.Warning,
                    contentDescription = null,
                    tint = Amber500,
                    modifier = Modifier.size(18.dp)
                )
                Text(
                    text = "You're checked in at ${checkedInLotCode ?: "another lot"}",
                    style = MaterialTheme.typography.bodySmall,
                    color = Amber500
                )
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Action buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Check In / Check Out button
            if (isCheckedInHere) {
                ActionButton(
                    text = "CHECK OUT",
                    onClick = onCheckOut,
                    isLoading = isLoading,
                    gradient = Brush.horizontalGradient(listOf(TextMuted, Black700)),
                    modifier = Modifier.weight(1f)
                )
            } else {
                ActionButton(
                    text = "CHECK IN",
                    onClick = onCheckIn,
                    isLoading = isLoading,
                    enabled = !isCheckedInElsewhere,
                    gradient = Brush.horizontalGradient(listOf(Blue500, Blue500.copy(alpha = 0.8f))),
                    modifier = Modifier.weight(1f)
                )
            }

            // Report TAPS button
            ActionButton(
                text = "REPORT TAPS",
                onClick = onReportTaps,
                isLoading = isLoading,
                gradient = Brush.horizontalGradient(listOf(Red500, Red500.copy(alpha = 0.8f))),
                modifier = Modifier.weight(1f)
            )
        }
    }
}

@Composable
private fun StatCard(
    label: String,
    value: String,
    icon: ImageVector,
    color: androidx.compose.ui.graphics.Color,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .background(Black700)
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = color,
            modifier = Modifier.size(24.dp)
        )
        Column {
            Text(
                text = value,
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = TextWhite
            )
            Text(
                text = label,
                style = MaterialTheme.typography.labelSmall,
                color = TextMuted,
                letterSpacing = 0.5.sp
            )
        }
    }
}

@Composable
private fun ActionButton(
    text: String,
    onClick: () -> Unit,
    isLoading: Boolean,
    gradient: Brush,
    modifier: Modifier = Modifier,
    enabled: Boolean = true
) {
    Box(
        modifier = modifier
            .height(48.dp)
            .clip(RoundedCornerShape(10.dp))
            .then(
                if (enabled) Modifier.background(gradient)
                else Modifier.background(Black700)
            )
            .clickable(enabled = enabled && !isLoading, onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        if (isLoading) {
            CircularProgressIndicator(
                modifier = Modifier.size(20.dp),
                color = TextWhite,
                strokeWidth = 2.dp
            )
        } else {
            Text(
                text = text,
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Bold,
                color = if (enabled) TextWhite else TextMuted,
                letterSpacing = 1.sp
            )
        }
    }
}

// Map style to hide POI icons (restaurants, museums, etc.)
private val hidePoiMapStyle = """
[
  {
    "featureType": "poi",
    "elementType": "labels.icon",
    "stylers": [
      {
        "visibility": "off"
      }
    ]
  },
  {
    "featureType": "poi.business",
    "stylers": [
      {
        "visibility": "off"
      }
    ]
  },
  {
    "featureType": "poi.attraction",
    "elementType": "labels.icon",
    "stylers": [
      {
        "visibility": "off"
      }
    ]
  },
  {
    "featureType": "poi.government",
    "elementType": "labels.icon",
    "stylers": [
      {
        "visibility": "off"
      }
    ]
  },
  {
    "featureType": "poi.medical",
    "elementType": "labels.icon",
    "stylers": [
      {
        "visibility": "off"
      }
    ]
  },
  {
    "featureType": "poi.place_of_worship",
    "elementType": "labels.icon",
    "stylers": [
      {
        "visibility": "off"
      }
    ]
  },
  {
    "featureType": "poi.school",
    "elementType": "labels.icon",
    "stylers": [
      {
        "visibility": "off"
      }
    ]
  },
  {
    "featureType": "poi.sports_complex",
    "elementType": "labels.icon",
    "stylers": [
      {
        "visibility": "off"
      }
    ]
  },
  {
    "featureType": "transit",
    "elementType": "labels.icon",
    "stylers": [
      {
        "visibility": "off"
      }
    ]
  }
]
""".trimIndent()
