---
title: Hugo Packet Management
---

The Hugo Packet is intended to be hosted in an S3-alike system, with packet items consisting either of files in the S3 bucket, or of distribution codes for publisher-provided downloads.

All items, be they files or codes, can be placed in "sections" to organize them on the page. The sections can be nested to an extent, which will allow for some minimal organizational options. The recommended way is to have a default top level section for the whole packet, and then one or more subsections for categories:

```
The Packet
- All Items section
- Best Dramatic Presentation section
  (all finalists item)
  - Finalists
    (individual finalist items)
- Best Fancast Section
  (all finalists item)
  - Finalists
    (individual finalist items)
- Best Game Section
  (individual finalist items)
```

# Packet Access

The packet has two states: disabled and enabled. A disabled packet is only accessible to preview users; an enabled packet is also accessible to any member with voting rights, while voting is open, and a link to it appears on the election page.

The packet view also requires the `SWITCH_HUGO_PACKET` waffle switch to be active, and the election to be in the Nominations Closed, Voting Preview, or Voting state. Outside of those, nobody sees the packet.

## Previewing the packet

Preview access is granted via the `hugopacket.preview_packet` permission ("Has early access to the packet"); assign it to users or groups via the Django admin in the usual way. Preview users can see the packet whether it is enabled or not, which is the intended way to review it before opening it up to the membership.

To get a preview URL to share with other preview users:

1. Navigate to `/admin/hugopacket/electionpacket/` and open the packet
2. Click "View on site" in the top right of the change form
3. Use that URL

## Enabling the packet

When you are ready to open the packet to voting members, edit the `ElectionPacket` in the admin and check the `enabled` field. Uncheck it to take the packet back out of circulation; preview users will still be able to see it.

Individual files also have their own `available` toggle on `PacketFile`. An unavailable file is hidden from everyone, including preview users, which is useful for pulling a single item without disabling the whole packet.

# System Configuration

The S3 connection configuration is system provided; NomNom only supports connections to one S3 endpoint for the packet.

Each packet must store all of its items in a single S3 bucket. That is configured when creating the packet, in the `s3_bucket_name` field.

## Settings

The convention settings in `config/settings.py` should configure some key values:

| Key                       | Type    | Notes                                                                                                                               |
|---------------------------|---------|-------------------------------------------------------------------------------------------------------------------------------------|
| `HUGOPACKET_AWS_REGION`   | String  | The AWS region for the packet. This will depend on the S3 provider.                                                                 |
| `HUGOPACKET_AWS_USE_CDN`  | Boolean | Enable this to use a CDN url for the packet items instead of direct signed S3 URLs.                                                 |
| `HUGOPACKET_AWS_ENDPOINT` | String  | Set this optionally to choose a packet AWS endpoint. By default this is set based on the region. Only used for DigitalOcean hosting |


## Environment

NomNom uses the AWS SDK's default connection configuration. That means that if you are using instance metadata to perform the connection, it should Just Work™. Rather than replicate that information here, please read [the AWS SDK documentation](https://docs.aws.amazon.com/sdkref/latest/guide/environment-variables.html) for that. Set those variables in your deployment environment, and the client will connect.

# Packet Files

A packet file has a name, description, and a position (which will be how it is shown relative to the other items in its section)

It also has an `S3 Object Key` which is the key in the bucket where the file can be found. This can be changed at any time.

## Creating a packet file item

1. Navigate to `/admin/hugopacket/packetfile/`
2. Select "Add Packet Item" from the top of the page
3. Fill in all mandatory fields
4. Select "Download (S3 file)" from the access type dropdown
5. Fill in the "S3 Object Key" field

# Distribution Codes

Distribution codes allow convention administrators to provide redeemable codes (such as game keys, digital book codes, or access tokens) to Hugo packet recipients. This system manages code pools, tracks distribution, and ensures each member receives a unique code for each item.

## Overview

When a packet item is configured as a CODE type, members view their assigned code instead of downloading a file. Each member receives exactly one code per item, and the system tracks which codes have been distributed to prevent duplication.

## Code Types

Common uses for distribution codes include:

- Game download keys: Steam, GOG, Epic Games Store, etc.
- Digital book access codes: Publishers' download portals
- Streaming access tokens: Temporary viewing codes
- Third-party platform codes: Any external service requiring unique identifiers

## Managing Distribution Codes

### Creating a Code Pool

1. Navigate to `/admin/hugopacket/distributioncode/`
2. Click Add Distribution Code
3. Fill in the required fields:
   - Packet item: Select the PacketFile this code belongs to
   - Code: The actual code string (alphanumeric recommended)
   - Assigned to: Leave blank (system assigns automatically)
4. Save the code

Repeat this process for each code in your pool.

### Bulk Import via CSV

For large code pools, use the CSV import feature:

1. Navigate to `/admin/hugopacket/packetfile/`
2. Click on the packet item that needs codes
3. In the "Distribution Codes" section (visible for CODE-type items), click Import codes from CSV
4. Prepare your CSV file in one of two formats:
   - Simple format: One code per line, no header
   - CSV with headers: Columns `code` and optional `notes`
5. Select your CSV file and click Upload

The import process:
- Skips empty codes
- Detects and skips duplicate codes within the upload
- Creates new codes that don't exist yet
- Updates notes on existing codes when CSV includes different notes
- Leaves existing codes unchanged if CSV has no note or same note

Simple Format Example (recommended for most uses):
```
ABC123DEF456
XYZ789GHI012
MNO345PQR678
```

CSV with Headers Example (use when you need notes):
```
code,notes
ABC123DEF456,Publisher batch 1
XYZ789GHI012,
MNO345PQR678,Replacement key
```

### Exporting Codes

To export existing codes (useful for auditing or backup):

1. Navigate to `/admin/hugopacket/distributioncode/`
2. Select the codes you want to export using checkboxes
3. From the "Action" dropdown, select Export selected codes to CSV
4. Click Go

The exported CSV includes:
- The code string
- Associated packet item
- Assignment status (member email if assigned, "Unassigned" otherwise)

## Packet Item Access

### Automatic Code Assignment

When a member accesses a CODE-type packet item:

1. System checks if member already has a code for this item
2. If yes, displays their existing code
3. If no, assigns the next available unassigned code from the pool
4. Records the assignment in the database

Once assigned, a member always sees the same code for a given item.

### No Access Limits

The Hugo Packet system does not enforce access limits for either CODE or DOWNLOAD type items. Members can:
- View their assigned codes as many times as needed
- Download files repeatedly without restrictions

The system tracks access counts for analytics and monitoring purposes, but never restricts access to content a member is entitled to view.

### Insufficient Codes

If all codes in a pool are assigned and a new member tries to access the item, they see an error page indicating no codes are available. Add more codes to the pool to resolve this.

## Code Display Formatting

Codes can optionally display with formatting to improve readability while preserving the raw code for copying.

### Setting a Display Format

1. Navigate to `/admin/hugopacket/packetfile/`
2. Edit the packet item
3. In the Code display format field, enter a template using `#` characters as placeholders
4. Save the item

Example:
- Raw code: `ABC12345DEF6789`
- Format template: `###-#####-###-####`
- Displayed to user: `ABC-12345-DEF-6789`

When a member clicks "Copy Code", they receive the raw code (`ABC12345DEF6789`) without separators.

### Format Rules

- Use `#` for alphanumeric character positions
- Use any other character as a separator (typically `-` or spaces)
- Codes shorter than the template stop at the last character (no trailing separators)
- Codes longer than the template are truncated to template length
- Non-alphanumeric characters in raw codes are stripped before formatting

## Monitoring Code Distribution

### View Assignment Status

1. Navigate to `/admin/hugopacket/distributioncode/`
2. Use filters:
   - By packet item: See all codes for a specific item
   - By assignment status: Filter assigned vs. unassigned codes
   - By member: Find which codes a specific member received

### Access Tracking

All member interactions with CODE items are recorded in PacketItemAccess records:

1. Navigate to `/admin/hugopacket/packetitemaccess/`
2. View:
   - Member who accessed the item
   - Packet item accessed
   - Assigned code (if any)
   - First access timestamp
   - Last access timestamp
   - Total view count

This data helps administrators:
- Verify code distribution
- Troubleshoot member issues ("I never received a code")
- Track engagement with packet materials
- Audit code usage for publisher reports

## Customization

Several templates are available to customize packet codes:

### `hugopacket/no_codes_available.html`

This template's `content` block can be replaced to configure the message when no more codes are available for the packet item. `packet_file` is provided to the template.

### `hugopacket/display_code.html`

This template's `content` block shows the code provided.

## Troubleshooting

### Member Reports Not Receiving a Code

1. Check if codes exist: `/admin/hugopacket/distributioncode/` filtered by packet item
2. Check member's access record: `/admin/hugopacket/packetitemaccess/` filtered by member
3. If no access record exists, member hasn't visited the item page yet
4. If access record exists without code, pool was empty at access time (add more codes)

### Duplicate Codes in Import

CSV import rejects items containing duplicate codes. Review your CSV for duplicates:
- Check for repeated lines
- Verify source data integrity
- Remove duplicates and retry import

### Code Already Exists

If import fails because codes already exist in the database:
1. Export existing codes via admin action
2. Compare with your import item
3. Remove duplicates from import file
4. Import only new codes

### Member Sees Wrong Code

The system guarantees code stability: once assigned, a member always sees the same code for an item. If a member reports seeing a different code:
- Verify they're logged into the correct account
- Check access records for their NominatingMemberProfile
- Confirm they're viewing the correct packet item (category/finalist)

## Best Practices

### Code Pool Sizing

- Count your expected Hugo packet recipients
- Inform the publisher of the member count; they will decide how many codes to provide
- Import all codes before making items visible to members

### Code Format Consistency

- Match publisher's recommended display format when applicable
- Test formatting with actual codes before finalizing

### Security Considerations

- Codes are visible in plain text to assigned members
- Treat code pools as sensitive data (do not commit to version control)
- Limit admin access to distribution code management
- Monitor access logs for unusual patterns

### Publisher Relations

- Track code assignment counts for publisher reporting
- Export assignment data regularly as backup
- Provide usage statistics to publishers post-convention
- Keep records of which codes were distributed vs. unused
