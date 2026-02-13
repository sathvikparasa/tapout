package com.warnabrotha.app.ui.screens

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import kotlinx.coroutines.launch
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlin.math.roundToInt
import com.google.android.gms.maps.CameraUpdateFactory
import com.google.android.gms.maps.model.BitmapDescriptorFactory
import com.google.android.gms.maps.model.CameraPosition
import com.google.android.gms.maps.model.LatLng
import com.google.android.gms.maps.model.MapStyleOptions
import com.google.maps.android.compose.*
import com.warnabrotha.app.data.model.ParkingLot
import com.warnabrotha.app.data.model.ParkingLotWithStats
import com.warnabrotha.app.data.model.ParkingSession
import com.warnabrotha.app.ui.theme.*

// UC Davis campus center coordinates
private val UC_DAVIS_CENTER = LatLng(38.5422, -121.7551)
private const val DEFAULT_ZOOM = 15.5f

// Hardcoded parking lot coordinates
private val PARKING_LOT_COORDINATES = mapOf(
    "MU" to LatLng(38.544416, -121.749561),
    "HUTCH" to LatLng(38.53969, -121.758182),
    "ARC" to LatLng(38.54304, -121.757572)
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
    var searchQuery by remember { mutableStateOf("") }

    val filteredLots = if (searchQuery.isBlank()) {
        parkingLots
    } else {
        parkingLots.filter {
            it.name.contains(searchQuery, ignoreCase = true) ||
                it.code.contains(searchQuery, ignoreCase = true)
        }
    }

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
            zoomControlsEnabled = false,
            compassEnabled = false,
            mapToolbarEnabled = false,
            myLocationButtonEnabled = false,
            rotationGesturesEnabled = true,
            scrollGesturesEnabled = true,
            tiltGesturesEnabled = true,
            zoomGesturesEnabled = true
        )
    }

    Box(modifier = modifier.fillMaxSize()) {
        // === Full-screen map ===
        GoogleMap(
            modifier = Modifier.fillMaxSize(),
            cameraPositionState = cameraPositionState,
            properties = mapProperties,
            uiSettings = mapUiSettings,
            onMapClick = { selectedLot = null }
        ) {
            filteredLots.forEach { lot ->
                val coordinates = PARKING_LOT_COORDINATES[lot.code]
                if (coordinates != null) {
                    val isSelected = selectedLot?.id == lot.id
                    Marker(
                        state = MarkerState(position = coordinates),
                        title = lot.name,
                        snippet = lot.code,
                        icon = BitmapDescriptorFactory.defaultMarker(
                            if (isSelected) BitmapDescriptorFactory.HUE_GREEN
                            else BitmapDescriptorFactory.HUE_GREEN - 30f
                        ),
                        alpha = if (isSelected) 1f else 0.7f,
                        onClick = {
                            selectedLot = lot
                            true
                        }
                    )
                }
            }
        }

        // === Floating search bar ===
        SearchBar(
            query = searchQuery,
            onQueryChange = { searchQuery = it },
            modifier = Modifier
                .align(Alignment.TopCenter)
                .statusBarsPadding()
                .padding(top = 8.dp, start = 16.dp, end = 16.dp)
        )

        // === Map control buttons (right side) ===
        val coroutineScope = rememberCoroutineScope()

        Column(
            modifier = Modifier
                .align(Alignment.CenterEnd)
                .padding(end = 16.dp)
                .width(IntrinsicSize.Min),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            MapControlButton(
                icon = Icons.Outlined.MyLocation,
                contentDescription = "My location",
                onClick = {
                    coroutineScope.launch {
                        cameraPositionState.animate(
                            CameraUpdateFactory.newLatLngZoom(UC_DAVIS_CENTER, DEFAULT_ZOOM)
                        )
                    }
                }
            )
            Column(
                modifier = Modifier
                    .width(48.dp)
                    .shadow(4.dp, RoundedCornerShape(12.dp))
                    .background(Surface, RoundedCornerShape(12.dp))
                    .border(1.dp, BorderLight, RoundedCornerShape(12.dp))
            ) {
                Box(
                    modifier = Modifier
                        .size(48.dp)
                        .clip(RoundedCornerShape(topStart = 12.dp, topEnd = 12.dp))
                        .clickable {
                            coroutineScope.launch {
                                cameraPositionState.animate(CameraUpdateFactory.zoomIn())
                            }
                        },
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.Add,
                        contentDescription = "Zoom in",
                        tint = TextSecondary,
                        modifier = Modifier.size(24.dp)
                    )
                }
                HorizontalDivider(color = BorderLight)
                Box(
                    modifier = Modifier
                        .size(48.dp)
                        .clip(RoundedCornerShape(bottomStart = 12.dp, bottomEnd = 12.dp))
                        .clickable {
                            coroutineScope.launch {
                                cameraPositionState.animate(CameraUpdateFactory.zoomOut())
                            }
                        },
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.Remove,
                        contentDescription = "Zoom out",
                        tint = TextSecondary,
                        modifier = Modifier.size(24.dp)
                    )
                }
            }
        }

        // === Swipeable bottom sheet ===
        val sheetOffsetY = remember { Animatable(0f) }
        val dismissThreshold = with(LocalDensity.current) { 120.dp.toPx() }

        // Reset offset when a new lot is selected
        LaunchedEffect(selectedLot) {
            sheetOffsetY.snapTo(0f)
        }

        if (selectedLot != null) {
            selectedLot?.let { lot ->
                val stats = lotStats[lot.id]
                val isCheckedInHere = currentSession?.parkingLotId == lot.id
                val isCheckedInElsewhere = currentSession != null && currentSession.parkingLotId != lot.id

                Box(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .offset { IntOffset(0, sheetOffsetY.value.roundToInt()) }
                        .pointerInput(Unit) {
                            detectVerticalDragGestures(
                                onDragEnd = {
                                    coroutineScope.launch {
                                        if (sheetOffsetY.value > dismissThreshold) {
                                            // Animate out then dismiss
                                            sheetOffsetY.animateTo(
                                                targetValue = size.height.toFloat(),
                                                animationSpec = tween(200)
                                            )
                                            selectedLot = null
                                        } else {
                                            // Snap back
                                            sheetOffsetY.animateTo(
                                                targetValue = 0f,
                                                animationSpec = tween(200)
                                            )
                                        }
                                    }
                                },
                                onVerticalDrag = { change, dragAmount ->
                                    change.consume()
                                    coroutineScope.launch {
                                        val newOffset = (sheetOffsetY.value + dragAmount)
                                            .coerceAtLeast(0f)
                                        sheetOffsetY.snapTo(newOffset)
                                    }
                                }
                            )
                        }
                ) {
                    LotBottomSheet(
                        lot = lot,
                        stats = stats,
                        isCheckedInHere = isCheckedInHere,
                        isCheckedInElsewhere = isCheckedInElsewhere,
                        checkedInLotCode = currentSession?.parkingLotCode,
                        isLoading = isLoading,
                        onCheckIn = { onCheckIn(lot.id) },
                        onCheckOut = onCheckOut,
                        onReportTaps = { onReportTaps(lot.id) }
                    )
                }
            }
        }
    }
}

// ─── Search Bar ───

@Composable
private fun SearchBar(
    query: String,
    onQueryChange: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .shadow(6.dp, RoundedCornerShape(12.dp), ambientColor = ShadowLight, spotColor = ShadowLight)
            .background(Surface.copy(alpha = 0.8f), RoundedCornerShape(12.dp))
            .border(1.dp, Border.copy(alpha = 0.5f), RoundedCornerShape(12.dp))
            .padding(horizontal = 12.dp, vertical = 5.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = Icons.Outlined.Search,
            contentDescription = null,
            tint = TextMuted,
            modifier = Modifier.padding(8.dp).size(24.dp)
        )

        BasicTextField(
            value = query,
            onValueChange = onQueryChange,
            singleLine = true,
            textStyle = MaterialTheme.typography.bodyMedium.copy(
                color = TextPrimary
            ),
            cursorBrush = SolidColor(Green500),
            modifier = Modifier
                .weight(1f)
                .padding(horizontal = 12.dp, vertical = 9.dp),
            decorationBox = { innerTextField ->
                if (query.isEmpty()) {
                    Text(
                        text = "Search campus lots...",
                        style = MaterialTheme.typography.bodyMedium,
                        color = TextMutedDark
                    )
                }
                innerTextField()
            }
        )

        if (query.isNotEmpty()) {
            IconButton(
                onClick = { onQueryChange("") },
                modifier = Modifier.size(32.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.Close,
                    contentDescription = "Clear search",
                    tint = TextMuted,
                    modifier = Modifier.size(18.dp)
                )
            }
        }
    }
}

// ─── Map control button ───

@Composable
private fun MapControlButton(
    icon: ImageVector,
    contentDescription: String,
    onClick: () -> Unit
) {
    Box(
        modifier = Modifier
            .size(48.dp)
            .shadow(4.dp, RoundedCornerShape(12.dp))
            .background(Surface, RoundedCornerShape(12.dp))
            .border(1.dp, BorderLight, RoundedCornerShape(12.dp))
            .clip(RoundedCornerShape(12.dp))
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        Icon(
            imageVector = icon,
            contentDescription = contentDescription,
            tint = TextSecondary,
            modifier = Modifier.size(24.dp)
        )
    }
}

// ─── Lot details bottom sheet ───

@Composable
private fun LotBottomSheet(
    lot: ParkingLot,
    stats: ParkingLotWithStats?,
    isCheckedInHere: Boolean,
    isCheckedInElsewhere: Boolean,
    checkedInLotCode: String?,
    isLoading: Boolean,
    onCheckIn: () -> Unit,
    onCheckOut: () -> Unit,
    onReportTaps: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .shadow(
                elevation = 10.dp,
                shape = RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp),
                ambientColor = ShadowLight,
                spotColor = ShadowLight
            )
            .background(Surface, RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp))
            .border(
                width = 1.dp,
                color = BorderLight,
                shape = RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp)
            )
            .padding(top = 17.dp, start = 24.dp, end = 24.dp, bottom = 32.dp)
            .navigationBarsPadding()
    ) {
        // Drag handle
        Box(
            modifier = Modifier
                .align(Alignment.CenterHorizontally)
                .width(48.dp)
                .height(4.dp)
                .background(Border, RoundedCornerShape(50))
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Title row: lot name + LIVE badge
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.Top
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "${lot.name} (${lot.code})",
                    style = MaterialTheme.typography.headlineLarge,
                    color = TextPrimary
                )
                Text(
                    text = "Zone ${lot.id} \u2022 UC Davis Campus",
                    style = MaterialTheme.typography.bodySmall.copy(
                        fontWeight = FontWeight.Medium
                    ),
                    color = TextSecondary
                )
            }

            // LIVE badge with background
            Box(
                modifier = Modifier
                    .background(GreenOverlay10, RoundedCornerShape(50))
                    .padding(horizontal = 10.dp, vertical = 4.dp)
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .background(Green500, CircleShape)
                    )
                    Text(
                        text = "LIVE",
                        style = MaterialTheme.typography.labelSmall,
                        color = Green500,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Stat cards
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            SheetStatCard(
                icon = Icons.Outlined.Group,
                value = "${stats?.activeParkers ?: 0}",
                label = "USERS CHECKED IN",
                modifier = Modifier.weight(1f)
            )
            SheetStatCard(
                icon = Icons.Outlined.TouchApp,
                value = "${stats?.recentSightings ?: 0}",
                label = "TAPS IN LAST HOUR",
                modifier = Modifier.weight(1f)
            )
        }

        // Checked in elsewhere warning
        if (isCheckedInElsewhere) {
            Spacer(modifier = Modifier.height(12.dp))
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(GreenOverlay5, RoundedCornerShape(8.dp))
                    .border(1.dp, Green500.copy(alpha = 0.2f), RoundedCornerShape(8.dp))
                    .padding(12.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Icon(
                    imageVector = Icons.Outlined.Info,
                    contentDescription = null,
                    tint = Green500,
                    modifier = Modifier.size(18.dp)
                )
                Text(
                    text = "You're checked in at ${checkedInLotCode ?: "another lot"}",
                    style = MaterialTheme.typography.bodySmall,
                    color = TextSecondary
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Action buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            if (isCheckedInHere) {
                SheetActionButton(
                    text = "CHECK OUT",
                    containerColor = TextSecondary,
                    onClick = onCheckOut,
                    isLoading = isLoading,
                    modifier = Modifier.weight(1f)
                )
            } else {
                SheetActionButton(
                    text = "CHECK IN",
                    containerColor = Green500,
                    onClick = onCheckIn,
                    isLoading = isLoading,
                    enabled = !isCheckedInElsewhere,
                    modifier = Modifier.weight(1f)
                )
            }
            SheetActionButton(
                text = "REPORT TAPS",
                containerColor = Red500,
                onClick = onReportTaps,
                isLoading = isLoading,
                modifier = Modifier.weight(1f)
            )
        }
    }
}

// ─── Stat card for bottom sheet ───

@Composable
private fun SheetStatCard(
    icon: ImageVector,
    value: String,
    label: String,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .background(Background, RoundedCornerShape(12.dp))
            .border(1.dp, GreenOverlay5, RoundedCornerShape(12.dp))
            .padding(13.dp),
        verticalArrangement = Arrangement.spacedBy(2.dp)
    ) {
        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = Green500,
                modifier = Modifier.size(18.dp)
            )
            Text(
                text = value,
                style = MaterialTheme.typography.headlineLarge,
                color = TextPrimary
            )
        }
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium.copy(
                fontWeight = FontWeight.SemiBold,
                letterSpacing = (-0.25).sp
            ),
            color = TextSecondary
        )
    }
}

// ─── Action button for bottom sheet ───

@Composable
private fun SheetActionButton(
    text: String,
    containerColor: Color,
    onClick: () -> Unit,
    isLoading: Boolean,
    modifier: Modifier = Modifier,
    enabled: Boolean = true
) {
    Box(
        modifier = modifier
            .height(44.dp)
            .shadow(
                if (enabled) 4.dp else 0.dp,
                RoundedCornerShape(12.dp),
                ambientColor = containerColor.copy(alpha = 0.3f),
                spotColor = containerColor.copy(alpha = 0.3f)
            )
            .clip(RoundedCornerShape(12.dp))
            .background(if (enabled) containerColor else containerColor.copy(alpha = 0.4f))
            .clickable(enabled = enabled && !isLoading, onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        if (isLoading) {
            CircularProgressIndicator(
                modifier = Modifier.size(18.dp),
                color = TextOnPrimary,
                strokeWidth = 2.dp
            )
        } else {
            Text(
                text = text,
                style = MaterialTheme.typography.titleSmall.copy(
                    fontFamily = DmSansFamily,
                    fontWeight = FontWeight.ExtraBold,
                    letterSpacing = 0.5.sp
                ),
                color = if (enabled) TextOnPrimary else TextOnPrimary.copy(alpha = 0.6f)
            )
        }
    }
}

// Map style to hide POI icons
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
